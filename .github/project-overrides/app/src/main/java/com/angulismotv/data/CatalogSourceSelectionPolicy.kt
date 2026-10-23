package com.angulismotv.data

/**
 * Resolves catalogue precedence without combining otherwise independent feeds.
 * A lower-priority feed is selected only when every higher-priority feed is empty.
 */
internal object CatalogSourceSelectionPolicy {
    enum class Source {
        PRIMARY,
        PERSONAL_FALLBACK,
        LEGACY_CHANNELS,
        LEGACY_EVENTS,
        NONE
    }

    data class Selection<T>(
        val source: Source,
        val channels: List<T>
    )

    fun <T> select(
        primary: List<T>,
        personal: List<T>,
        legacyChannels: List<T>,
        legacyEvents: List<T>
    ): Selection<T> = when {
        primary.isNotEmpty() -> Selection(Source.PRIMARY, primary)
        personal.isNotEmpty() -> Selection(Source.PERSONAL_FALLBACK, personal)
        legacyChannels.isNotEmpty() -> Selection(Source.LEGACY_CHANNELS, legacyChannels)
        legacyEvents.isNotEmpty() -> Selection(Source.LEGACY_EVENTS, legacyEvents)
        else -> Selection(Source.NONE, emptyList())
    }
}
