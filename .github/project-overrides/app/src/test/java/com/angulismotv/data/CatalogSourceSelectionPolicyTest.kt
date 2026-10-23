package com.angulismotv.data

import org.junit.Assert.assertEquals
import org.junit.Test

class CatalogSourceSelectionPolicyTest {
    @Test
    fun primaryCatalogueWinsWithoutAppendingPersonalChannels() {
        val selection = CatalogSourceSelectionPolicy.select(
            primary = listOf("primary-1", "primary-2"),
            personal = listOf("personal-1"),
            legacyChannels = listOf("legacy-1"),
            legacyEvents = listOf("event-1")
        )

        assertEquals(CatalogSourceSelectionPolicy.Source.PRIMARY, selection.source)
        assertEquals(listOf("primary-1", "primary-2"), selection.channels)
    }

    @Test
    fun personalCatalogueIsUsedOnlyWhenPrimaryIsEmpty() {
        val selection = CatalogSourceSelectionPolicy.select(
            primary = emptyList(),
            personal = listOf("personal-1", "personal-2"),
            legacyChannels = listOf("legacy-1"),
            legacyEvents = listOf("event-1")
        )

        assertEquals(CatalogSourceSelectionPolicy.Source.PERSONAL_FALLBACK, selection.source)
        assertEquals(listOf("personal-1", "personal-2"), selection.channels)
    }

    @Test
    fun legacyChannelFeedIsTheNextFallback() {
        val selection = CatalogSourceSelectionPolicy.select(
            primary = emptyList(),
            personal = emptyList(),
            legacyChannels = listOf("legacy-1"),
            legacyEvents = listOf("event-1")
        )

        assertEquals(CatalogSourceSelectionPolicy.Source.LEGACY_CHANNELS, selection.source)
        assertEquals(listOf("legacy-1"), selection.channels)
    }

    @Test
    fun eventsFeedIsUsedOnlyWhenEveryEarlierFeedIsEmpty() {
        val selection = CatalogSourceSelectionPolicy.select(
            primary = emptyList(),
            personal = emptyList(),
            legacyChannels = emptyList(),
            legacyEvents = listOf("event-1")
        )

        assertEquals(CatalogSourceSelectionPolicy.Source.LEGACY_EVENTS, selection.source)
        assertEquals(listOf("event-1"), selection.channels)
    }

    @Test
    fun allEmptyFeedsProduceNoCatalogue() {
        val selection = CatalogSourceSelectionPolicy.select<String>(
            primary = emptyList(),
            personal = emptyList(),
            legacyChannels = emptyList(),
            legacyEvents = emptyList()
        )

        assertEquals(CatalogSourceSelectionPolicy.Source.NONE, selection.source)
        assertEquals(emptyList<String>(), selection.channels)
    }
}
