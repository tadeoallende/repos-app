package com.angulismotv.data

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class IptvOrgPlaylistPolicyTest {
    @Test
    fun blankSourceResolvesToGlobalIndexForRegionalFiltering() {
        assertEquals(
            IptvOrgPlaylistPolicy.DEFAULT_PLAYLIST_URL,
            IptvOrgPlaylistPolicy.resolve("")
        )
    }

    @Test
    fun officialIptvOrgPlaylistsNormalizeToGlobalIndex() {
        listOf(
            "https://iptv-org.github.io/iptv/countries/ar.m3u",
            "https://iptv-org.github.io/iptv/countries/br.m3u",
            "https://iptv-org.github.io/iptv/index.m3u"
        ).forEach { url ->
            assertEquals(IptvOrgPlaylistPolicy.DEFAULT_PLAYLIST_URL, IptvOrgPlaylistPolicy.resolve(url))
            assertTrue(IptvOrgPlaylistPolicy.shouldApplyAmericasFilter(url))
        }
    }

    @Test
    fun customM3uUrlsArePreservedAndDoNotInheritIptvOrgRegionalFilter() {
        val custom = "https://feeds.example/channels.m3u"
        assertEquals(custom, IptvOrgPlaylistPolicy.resolve(custom))
        assertFalse(IptvOrgPlaylistPolicy.shouldApplyAmericasFilter(custom))
    }

    @Test
    fun disabledSourceRemainsDisabled() {
        assertEquals("", IptvOrgPlaylistPolicy.resolve("disabled"))
        assertFalse(IptvOrgPlaylistPolicy.shouldApplyAmericasFilter("disabled"))
    }
}
