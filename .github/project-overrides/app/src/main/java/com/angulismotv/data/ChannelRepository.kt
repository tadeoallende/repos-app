package com.angulismotv.data

import android.content.Context
import android.util.Log
import com.angulismotv.BuildConfig
import com.angulismotv.models.Channel
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.withContext
import java.io.File
import java.io.IOException

/** Result of loading the configured feeds. */
data class LoadResult(
    val channels: List<Channel>,
    val failed: Boolean = false,
    val notConfigured: Boolean = false,
    /** True when usable data loaded, but at least one configured source failed. */
    val partialFailure: Boolean = false,
    /** Human-readable internal diagnostic label for the source selected by the repository. */
    val sourceName: String? = null
)

/** Loads the regional IPTV-org catalogue plus the personal catalogue, keeping legacy fallbacks. */
object ChannelRepository {
    private val iptvOrgDataSource by lazy(LazyThreadSafetyMode.SYNCHRONIZED) { IptvOrgDataSource() }
    private val fallbackDataSource by lazy(LazyThreadSafetyMode.SYNCHRONIZED) { ChannelFeedDataSource() }
    private val gson by lazy(LazyThreadSafetyMode.SYNCHRONIZED) { Gson() }
    private val cacheType = object : TypeToken<List<Channel>>() {}.type
    private const val CACHE_FILE = "channel_catalog_cache.json"

    private data class SourceLoad(
        val url: String,
        val result: Result<List<Channel>>,
        val channels: List<Channel>
    )

    /** Lee y recupera el último catálogo bueno guardado localmente, sin copiar el JSON entero a memoria. */
    suspend fun loadCached(context: Context): LoadResult? = withContext(Dispatchers.IO) {
        runCatching {
            val directory = context.applicationContext.filesDir
            val target = File(directory, CACHE_FILE)
            val backup = File(directory, "$CACHE_FILE.bak")
            listOf(target, backup).firstNotNullOfOrNull { file ->
                if (!file.isFile || file.length() <= 2L) return@firstNotNullOfOrNull null
                val channels = runCatching {
                    file.bufferedReader(Charsets.UTF_8).use { reader ->
                        gson.fromJson<List<Channel>>(reader, cacheType)
                    }
                }.getOrNull().orEmpty()
                if (channels.isEmpty()) return@firstNotNullOfOrNull null

                if (file == backup && (!target.exists() || target.delete())) {
                    if (!backup.renameTo(target)) {
                        Log.w(TAG, "Se recuperó la caché de respaldo en memoria, pero no se pudo restaurar el archivo")
                    }
                }
                LoadResult(channels, sourceName = "Caché local")
            }
        }.onFailure { Log.w(TAG, "No se pudo leer la caché local (" + it.javaClass.simpleName + ")") }.getOrNull()
    }

    suspend fun loadAll(context: Context? = null): LoadResult = coroutineScope {
        // Fetch the regional catalogue and user-maintained feed concurrently.
        val primaryDeferred = async { loadPrimarySource() }
        val personalDeferred = async { loadPersonalSource() }
        val primary = primaryDeferred.await()
        val personal = personalDeferred.await()

        if (primary.channels.isNotEmpty()) {
            val merged = withContext(Dispatchers.Default) {
                (primary.channels + personal.channels).distinctChannels()
            }
            if (context != null && merged.isNotEmpty()) saveCache(context, merged)
            Log.i(TAG, "Canales cargados: IPTV-org=" + primary.channels.size + ", propios=" + personal.channels.size)
            return@coroutineScope LoadResult(
                channels = merged,
                partialFailure = personal.url.isNotBlank() && personal.result.isFailure,
                sourceName = if (personal.channels.isNotEmpty()) "IPTV-org + canales propios" else "IPTV-org"
            )
        }

        logPrimarySourceFailure(primary)
        loadFallbackSources(primary, personal, context)
    }

    private suspend fun loadPrimarySource(): SourceLoad {
        val configuredUrl = BuildConfig.IPTV_ORG_URL.trim()
        val url = IptvOrgPlaylistPolicy.resolve(configuredUrl)
        val result = if (url.isBlank()) Result.success(emptyList()) else iptvOrgDataSource.load(url)
        val parsed = result.getOrDefault(emptyList())
        val scoped = withContext(Dispatchers.Default) {
            val regional = if (IptvOrgPlaylistPolicy.shouldApplyAmericasFilter(configuredUrl)) {
                ChannelRegionPolicy.filter(parsed)
            } else parsed
            regional.distinctChannels()
        }
        return SourceLoad(url, result, scoped)
    }

    private suspend fun loadPersonalSource(): SourceLoad {
        val configured = BuildConfig.CUSTOM_CHANNELS_URL.trim()
        val url = if (configured.equals("disabled", ignoreCase = true)) "" else configured
        val result = fallbackDataSource.load(url, defaultCategory = "Personalizados")
        val channels = withContext(Dispatchers.Default) { result.getOrDefault(emptyList()).distinctChannels() }
        return SourceLoad(url, result, channels)
    }

    private fun logPrimarySourceFailure(primary: SourceLoad) {
        if (primary.result.isFailure) {
            Log.w(TAG, "IPTV-org no disponible; se intentarán las fuentes de respaldo")
        } else if (primary.url.isNotBlank()) {
            Log.w(TAG, "IPTV-org no devolvió canales de América o cadenas internacionales; se intentarán las fuentes de respaldo")
        }
    }

    private suspend fun loadFallbackSources(primary: SourceLoad, personal: SourceLoad, context: Context?): LoadResult = coroutineScope {
        val channelsUrl = BuildConfig.CHANNELS_URL.trim()
        val eventsUrl = BuildConfig.EVENTS_URL.trim()
        val direct = async { fallbackDataSource.load(channelsUrl, defaultCategory = "todos") }
        val events = async { fallbackDataSource.load(eventsUrl, defaultCategory = "deportes") }
        val results = listOf(direct.await(), events.await())
        val legacyChannels = results.flatMap { it.getOrDefault(emptyList()) }
        val channels = withContext(Dispatchers.Default) {
            (legacyChannels + personal.channels).distinctChannels()
        }
        if (context != null && channels.isNotEmpty()) saveCache(context, channels)
        val legacyFailure = (channelsUrl.isNotBlank() && results[0].isFailure) ||
            (eventsUrl.isNotBlank() && results[1].isFailure)
        val primaryFailed = primary.url.isNotBlank() && primary.result.isFailure
        val personalFailed = personal.url.isNotBlank() && personal.result.isFailure
        val anyConfigured = primary.url.isNotBlank() || channelsUrl.isNotBlank() ||
            eventsUrl.isNotBlank() || personal.url.isNotBlank()

        LoadResult(
            channels = channels,
            failed = channels.isEmpty() && (primaryFailed || legacyFailure || personalFailed),
            notConfigured = channels.isEmpty() && !anyConfigured,
            partialFailure = channels.isNotEmpty() && (primaryFailed || legacyFailure || personalFailed),
            sourceName = when {
                legacyChannels.isNotEmpty() && personal.channels.isNotEmpty() -> "Fuentes de respaldo + canales propios"
                personal.channels.isNotEmpty() -> "Canales propios"
                legacyChannels.isNotEmpty() -> "Fuentes propias (respaldo)"
                else -> null
            }
        )
    }

    private suspend fun saveCache(context: Context, channels: List<Channel>) = withContext(Dispatchers.IO) {
        runCatching {
            val directory = context.applicationContext.filesDir
            val target = File(directory, CACHE_FILE)
            val temporary = File(directory, "$CACHE_FILE.tmp")
            val backup = File(directory, "$CACHE_FILE.bak")
            temporary.bufferedWriter(Charsets.UTF_8).use { writer -> gson.toJson(channels, cacheType, writer) }

            // Keep the previous valid cache until the replacement file is ready to become the target.
            if (target.exists()) {
                if (backup.exists() && !backup.delete()) {
                    throw IOException("No se pudo limpiar la copia anterior de la caché")
                }
                if (!target.renameTo(backup)) throw IOException("No se pudo respaldar la caché anterior")
            }

            if (!temporary.renameTo(target)) {
                // Restore the previous catalogue if the final rename fails.
                if (!target.exists() && backup.exists()) backup.renameTo(target)
                throw IOException("No se pudo guardar la caché de canales")
            }
            if (backup.exists() && !backup.delete()) {
                Log.w(TAG, "Se guardó la caché nueva, pero no se pudo eliminar la copia de respaldo")
            }
        }.onFailure { Log.w(TAG, "No se pudo guardar la caché local (" + it.javaClass.simpleName + ")") }
    }

    private fun List<Channel>.distinctChannels(): List<Channel> =
        distinctBy(ChannelCatalog::feedDeduplicationKey)

    private const val TAG = "ChannelRepository"
}
