package com.angulismotv.data

import org.junit.Assert.assertEquals
import org.junit.Test

class CatalogSourceSelectionPolicyTest {
    @Test
    fun personalCatalogueIsAuthoritativeAndDoesNotAppendIptvOrgChannels() {
        val selection = CatalogSourceSelectionPolicy.select(
            personal = listOf("personal-1", "personal-2"),
            iptvOrgFallback = listOf("iptv-1"),
            legacyChannels = listOf("legacy-1"),
            legacyEvents = listOf("event-1")
        )

        assertEquals(CatalogSourceSelectionPolicy.Source.PERSONAL, selection.source)
        assertEquals(listOf("personal-1", "personal-2"), selection.channels)
    }

    @Test
    fun iptvOrgIsUsedOnlyWhenPersonalCatalogueIsEmpty() {
        val selection = CatalogSourceSelectionPolicy.select(
            personal = emptyList(),
            iptvOrgFallback = listOf("iptv-1", "iptv-2"),
            legacyChannels = listOf("legacy-1"),
            legacyEvents = listOf("event-1")
        )

        assertEquals(CatalogSourceSelectionPolicy.Source.IPTV_ORG_FALLBACK, selection.source)
        assertEquals(listOf("iptv-1", "iptv-2"), selection.channels)
    }

    @Test
    fun legacyChannelFeedIsTheNextFallback() {
        val selection = CatalogSourceSelectionPolicy.select(
            personal = emptyList(),
            iptvOrgFallback = emptyList(),
            legacyChannels = listOf("legacy-1"),
            legacyEvents = listOf("event-1")
        )

        assertEquals(CatalogSourceSelectionPolicy.Source.LEGACY_CHANNELS, selection.source)
        assertEquals(listOf("legacy-1"), selection.channels)
    }

    @Test
    fun eventsFeedIsUsedOnlyWhenEveryEarlierFeedIsEmpty() {
        val selection = CatalogSourceSelectionPolicy.select(
            personal = emptyList(),
            iptvOrgFallback = emptyList(),
            legacyChannels = emptyList(),
            legacyEvents = listOf("event-1")
        )

        assertEquals(CatalogSourceSelectionPolicy.Source.LEGACY_EVENTS, selection.source)
        assertEquals(listOf("event-1"), selection.channels)
    }

    @Test
    fun allEmptyFeedsProduceNoCatalogue() {
        val selection = CatalogSourceSelectionPolicy.select<String>(
            personal = emptyList(),
            iptvOrgFallback = emptyList(),
            legacyChannels = emptyList(),
            legacyEvents = emptyList()
        )

        assertEquals(CatalogSourceSelectionPolicy.Source.NONE, selection.source)
        assertEquals(emptyList<String>(), selection.channels)
    }
}
