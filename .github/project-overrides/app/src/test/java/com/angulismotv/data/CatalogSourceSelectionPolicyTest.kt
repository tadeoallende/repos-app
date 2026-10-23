package com.angulismotv.data

import org.junit.Assert.assertEquals
import org.junit.Test

class CatalogSourceSelectionPolicyTest {
    @Test
    fun legacyChannelFeedWinsWhenBothLegacyFeedsHaveData() {
        val selection = CatalogSourceSelectionPolicy.select(
            legacyChannels = listOf("legacy-1", "legacy-2"),
            legacyEvents = listOf("event-1")
        )

        assertEquals(CatalogSourceSelectionPolicy.Source.LEGACY_CHANNELS, selection.source)
        assertEquals(listOf("legacy-1", "legacy-2"), selection.channels)
    }

    @Test
    fun eventsFeedIsUsedWhenLegacyChannelFeedIsEmpty() {
        val selection = CatalogSourceSelectionPolicy.select(
            legacyChannels = emptyList(),
            legacyEvents = listOf("event-1")
        )

        assertEquals(CatalogSourceSelectionPolicy.Source.LEGACY_EVENTS, selection.source)
        assertEquals(listOf("event-1"), selection.channels)
    }

    @Test
    fun allLegacyFeedsEmptyProduceNoCatalogue() {
        val selection = CatalogSourceSelectionPolicy.select<String>(
            legacyChannels = emptyList(),
            legacyEvents = emptyList()
        )

        assertEquals(CatalogSourceSelectionPolicy.Source.NONE, selection.source)
        assertEquals(emptyList<String>(), selection.channels)
    }
}
