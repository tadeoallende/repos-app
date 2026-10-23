package com.angulismotv.data

/**
 * Resolves catalogue precedence without combining independent feeds.
 * The personal catalogue is authoritative; IPTV-org is the first fallback.
 */
internal object CatalogSourceSelectionPolicy {
    enum class Source {
        PERSONAL,
        IPTV_ORG_FALLBACK,
        LEGACY_CHANNELS,
        LEGACY_EVENTS,
        NONE
    }

    data class Selection<T>(
        val source: Source,
        val channels: List<T>
    )

    fun <T> select(
        personal: List<T>,
        iptvOrgFallback: List<T>,
        legacyChannels: List<T>,
        legacyEvents: List<T>
    ): Selection<T> = when {
        personal.isNotEmpty() -> Selection(Source.PERSONAL, personal)
        iptvOrgFallback.isNotEmpty() -> Selection(Source.IPTV_ORG_FALLBACK, iptvOrgFallback)
        legacyChannels.isNotEmpty() -> Selection(Source.LEGACY_CHANNELS, legacyChannels)
        legacyEvents.isNotEmpty() -> Selection(Source.LEGACY_EVENTS, legacyEvents)
        else -> Selection(Source.NONE, emptyList())
    }
}
