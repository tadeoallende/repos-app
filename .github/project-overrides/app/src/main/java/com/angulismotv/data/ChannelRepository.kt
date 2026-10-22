package com.angulismotv.data

import android.util.Log
import com.angulismotv.BuildConfig
import com.angulismotv.models.Channel
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope

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

    private data class SourceLoad(
        val url: String,
        val result: Result<List<Channel>>,
        val channels: List<Channel>
    )

    suspend fun loadAll(): LoadResult = coroutineScope {
        // Fetch the regional catalogue and user-maintained feed concurrently.
        val primaryDeferred = async { loadPrimarySource() }
        val personalDeferred = async { loadPersonalSource() }
        val primary = primaryDeferred.await()
        val personal = personalDeferred.await()

        if (primary.channels.isNotEmpty()) {
            val merged = (primary.channels + personal.channels).distinctChannels()
            Log.i(TAG, "Canales cargados: IPTV-org=${primary.channels.size}, propios=${personal.channels.size}")
            return@coroutineScope LoadResult(
                channels = merged,
                partialFailure = personal.url.isNotBlank() && personal.result.isFailure,
                sourceName = if (personal.channels.isNotEmpty()) "IPTV-org + canales propios" else "IPTV-org"
            )
        }

        logPrimarySourceFailure(primary)
        loadFallbackSources(primary, personal)
    }

    private suspend fun loadPrimarySource(): SourceLoad {
        val configuredUrl = BuildConfig.IPTV_ORG_URL.trim()
        val url = IptvOrgPlaylistPolicy.resolve(configuredUrl)
        val result = if (url.isBlank()) Result.success(emptyList()) else iptvOrgDataSource.load(url)
        val parsed = result.getOrDefault(emptyList())
        val scoped = if (IptvOrgPlaylistPolicy.shouldApplyAmericasFilter(configuredUrl)) {
            ChannelRegionPolicy.filter(parsed)
        } else {
            parsed
        }
        return SourceLoad(url, result, scoped.distinctChannels())
    }

    private suspend fun loadPersonalSource(): SourceLoad {
        val configured = BuildConfig.CUSTOM_CHANNELS_URL.trim()
        val url = if (configured.equals("disabled", ignoreCase = true)) "" else configured
        val result = fallbackDataSource.load(url, defaultCategory = "Personalizados")
        return SourceLoad(url, result, result.getOrDefault(emptyList()).distinctChannels())
    }

    private fun logPrimarySourceFailure(primary: SourceLoad) {
        if (primary.result.isFailure) {
            Log.w(TAG, "IPTV-org no disponible; se intentarán las fuentes de respaldo")
        } else if (primary.url.isNotBlank()) {
            Log.w(TAG, "IPTV-org no devolvió canales de América o cadenas internacionales; se intentarán las fuentes de respaldo")
        }
    }

    private suspend fun loadFallbackSources(primary: SourceLoad, personal: SourceLoad): LoadResult = coroutineScope {
        val channelsUrl = BuildConfig.CHANNELS_URL.trim()
        val eventsUrl = BuildConfig.EVENTS_URL.trim()
        val direct = async { fallbackDataSource.load(channelsUrl, defaultCategory = "todos") }
        val events = async { fallbackDataSource.load(eventsUrl, defaultCategory = "deportes") }
        val results = listOf(direct.await(), events.await())
        val legacyChannels = results.flatMap { it.getOrDefault(emptyList()) }
        val channels = (legacyChannels + personal.channels).distinctChannels()
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

    private fun List<Channel>.distinctChannels(): List<Channel> =
        distinctBy(ChannelCatalog::feedDeduplicationKey)

    private const val TAG = "ChannelRepository"
}
