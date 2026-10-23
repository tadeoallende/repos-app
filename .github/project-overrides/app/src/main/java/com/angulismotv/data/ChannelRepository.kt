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

/** Loads one preferred catalogue and tries the next tier only when the current tier is unusable. */
object ChannelRepository {
    private val iptvOrgDataSource by lazy(LazyThreadSafetyMode.SYNCHRONIZED) { IptvOrgDataSource() }
    private val fallbackDataSource by lazy(LazyThreadSafetyMode.SYNCHRONIZED) { ChannelFeedDataSource() }
    private val gson by lazy(LazyThreadSafetyMode.SYNCHRONIZED) { Gson() }
    private val cacheType = object : TypeToken<List<Channel>>() {}.type
    private const val CACHE_FILE = "channel_catalog_cache.json"

    private data class SourceLoad(
        val url: String,
        val result: Result<List<Channel>>,
        val channels: List<Channel>,
        val name: String = ""
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

    suspend fun loadAll(context: Context? = null): LoadResult {
        // El catálogo personal es la fuente principal. Las fuentes externas se consultan
        // solamente cuando no entrega canales utilizables.
        val personal = loadPersonalSource()
        if (personal.channels.isNotEmpty()) {
            if (context != null) saveCache(context, personal.channels)
            Log.i(TAG, "Canales cargados desde el catálogo personal: ${personal.channels.size}")
            return LoadResult(
                channels = personal.channels,
                sourceName = "Canales propios"
            )
        }

        logPersonalSourceFailure(personal)

        val iptvOrgFallback = loadPrimarySource(context)
        if (iptvOrgFallback.channels.isNotEmpty()) {
            if (context != null) saveCache(context, iptvOrgFallback.channels)
            val personalUnavailable = personal.isUnavailable()
            Log.i(TAG, "Se usa IPTV-org como respaldo: ${iptvOrgFallback.channels.size} canales")
            return LoadResult(
                channels = iptvOrgFallback.channels,
                partialFailure = personalUnavailable,
                sourceName = "${iptvOrgFallback.name.ifBlank { "IPTV-org" }} (respaldo)"
            )
        }

        logIptvOrgFallbackFailure(iptvOrgFallback)
        return loadFallbackSources(iptvOrgFallback, personal, context)
    }

    private suspend fun loadPrimarySource(context: Context?): SourceLoad {
        val remoteSource = RemoteSourceConfiguration.load(context)
        val configuredUrl = if (remoteSource.enabled) remoteSource.url else "disabled"
        val url = IptvOrgPlaylistPolicy.resolve(configuredUrl)
        val result = if (url.isBlank()) Result.success(emptyList()) else iptvOrgDataSource.load(url)
        val parsed = result.getOrDefault(emptyList())
        val scoped = withContext(Dispatchers.Default) {
            val regional = if (IptvOrgPlaylistPolicy.shouldApplyAmericasFilter(configuredUrl)) {
                ChannelRegionPolicy.filter(parsed)
            } else parsed
            regional.distinctChannels()
        }
        return SourceLoad(url, result, scoped, remoteSource.name)
    }

    private suspend fun loadPersonalSource(): SourceLoad {
        val configured = BuildConfig.CUSTOM_CHANNELS_URL.trim()
        val url = if (configured.equals("disabled", ignoreCase = true)) "" else configured
        val result = fallbackDataSource.load(url, defaultCategory = "Personalizados")
        val channels = withContext(Dispatchers.Default) { result.getOrDefault(emptyList()).distinctChannels() }
        return SourceLoad(url, result, channels)
    }

    private fun logPersonalSourceFailure(personal: SourceLoad) {
        if (personal.result.isFailure) {
            Log.w(TAG, "El catálogo personal no está disponible; se intentará IPTV-org como respaldo")
        } else if (personal.url.isNotBlank() && personal.channels.isEmpty()) {
            Log.w(TAG, "El catálogo personal no devolvió canales válidos; se intentará IPTV-org como respaldo")
        }
    }

    private fun logIptvOrgFallbackFailure(source: SourceLoad) {
        if (source.result.isFailure) {
            Log.w(TAG, "IPTV-org no está disponible; se intentarán las fuentes heredadas de respaldo")
        } else if (source.url.isNotBlank() && source.channels.isEmpty()) {
            Log.w(TAG, "IPTV-org no devolvió canales válidos; se intentarán las fuentes heredadas")
        }
    }

    private suspend fun loadFallbackSources(
        iptvOrgFallback: SourceLoad,
        personal: SourceLoad,
        context: Context?
    ): LoadResult = coroutineScope {
        val channelsUrl = BuildConfig.CHANNELS_URL.trim()
        val eventsUrl = BuildConfig.EVENTS_URL.trim()
        val channelsDeferred = async { fallbackDataSource.load(channelsUrl, defaultCategory = "todos") }
        val eventsDeferred = async { fallbackDataSource.load(eventsUrl, defaultCategory = "deportes") }
        val channelsResult = channelsDeferred.await()
        val eventsResult = eventsDeferred.await()

        val legacyChannels = withContext(Dispatchers.Default) {
            channelsResult.getOrDefault(emptyList()).distinctChannels()
        }
        val legacyEvents = withContext(Dispatchers.Default) {
            eventsResult.getOrDefault(emptyList()).distinctChannels()
        }
        val legacyChannelSource = SourceLoad(channelsUrl, channelsResult, legacyChannels, "Catálogo alternativo")
        val legacyEventSource = SourceLoad(eventsUrl, eventsResult, legacyEvents, "Eventos deportivos")
        val selection = CatalogSourceSelectionPolicy.select(
            personal = personal.channels,
            iptvOrgFallback = iptvOrgFallback.channels,
            legacyChannels = legacyChannelSource.channels,
            legacyEvents = legacyEventSource.channels
        )
        val channels = selection.channels

        if (context != null && channels.isNotEmpty()) saveCache(context, channels)

        val personalUnavailable = personal.isUnavailable()
        val iptvUnavailable = iptvOrgFallback.isUnavailable()
        val legacyChannelsUnavailable = legacyChannelSource.isUnavailable()
        val legacyEventsUnavailable = legacyEventSource.isUnavailable()
        val anyConfigured = listOf(personal.url, iptvOrgFallback.url, channelsUrl, eventsUrl)
            .any { it.isNotBlank() }
        val anyUnavailable = personalUnavailable || iptvUnavailable ||
            legacyChannelsUnavailable || legacyEventsUnavailable
        val upstreamFailure = when (selection.source) {
            CatalogSourceSelectionPolicy.Source.PERSONAL -> false
            CatalogSourceSelectionPolicy.Source.IPTV_ORG_FALLBACK -> personalUnavailable
            CatalogSourceSelectionPolicy.Source.LEGACY_CHANNELS ->
                personalUnavailable || iptvUnavailable
            CatalogSourceSelectionPolicy.Source.LEGACY_EVENTS ->
                personalUnavailable || iptvUnavailable || legacyChannelsUnavailable
            CatalogSourceSelectionPolicy.Source.NONE -> false
        }

        LoadResult(
            channels = channels,
            failed = channels.isEmpty() && anyConfigured && anyUnavailable,
            notConfigured = channels.isEmpty() && !anyConfigured,
            partialFailure = channels.isNotEmpty() && upstreamFailure,
            sourceName = when (selection.source) {
                CatalogSourceSelectionPolicy.Source.PERSONAL -> "Canales propios"
                CatalogSourceSelectionPolicy.Source.IPTV_ORG_FALLBACK ->
                    "${iptvOrgFallback.name.ifBlank { "IPTV-org" }} (respaldo)"
                CatalogSourceSelectionPolicy.Source.LEGACY_CHANNELS -> "Catálogo alternativo (respaldo)"
                CatalogSourceSelectionPolicy.Source.LEGACY_EVENTS -> "Eventos deportivos (respaldo)"
                CatalogSourceSelectionPolicy.Source.NONE -> null
            }
        )
    }

    private fun SourceLoad.isUnavailable(): Boolean =
        url.isNotBlank() && (result.isFailure || channels.isEmpty())

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
