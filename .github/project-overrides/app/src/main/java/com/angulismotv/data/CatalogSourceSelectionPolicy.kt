package com.angulismotv.data

/**
 * Selects between the legacy feeds after the personal and IPTV-org catalogues
 * have already been checked by ChannelRepository. Never combines feed contents.
 */
internal object CatalogSourceSelectionPolicy {
    enum class Source {
        LEGACY_CHANNELS,
        LEGACY_EVENTS,
        NONE
    }

    data class Selection<T>(
        val source: Source,
        val channels: List<T>
    )

    fun <T> select(
        legacyChannels: List<T>,
        legacyEvents: List<T>
    ): Selection<T> = when {
        legacyChannels.isNotEmpty() -> Selection(Source.LEGACY_CHANNELS, legacyChannels)
        legacyEvents.isNotEmpty() -> Selection(Source.LEGACY_EVENTS, legacyEvents)
        else -> Selection(Source.NONE, emptyList())
    }
}
