package com.angulismotv.player

import com.angulismotv.models.Channel
import com.angulismotv.models.StreamType
import org.junit.Assert.assertEquals
import org.junit.Assert.assertSame
import org.junit.Test

class PlayerLaunchRequestFactoryTest {

    @Test
    fun resolvesByStableChannelIdentityAndKeepsFirstMatchingIndex() {
        val original = Channel(name = "Sports HD", streamUrl = "https://example.test/live.m3u8", streamType = StreamType.HLS)
        val second = Channel(name = "News", streamUrl = "https://example.test/news.m3u8", streamType = StreamType.HLS)
        val sameStreamRenamed = Channel(name = "Sports", streamUrl = original.streamUrl, streamType = original.streamType)

        val result = PlayerLaunchRequestFactory.resolveCatalog(listOf(original, second), sameStreamRenamed)

        assertEquals(0, result.channelIndex)
        assertEquals(2, result.channels.size)
        assertSame(original, result.channels[0])
        assertSame(second, result.channels[1])
    }

    @Test
    fun appendsStaleChannelRatherThanSubstitutingFirstCatalogItem() {
        val existing = Channel(name = "Existing", streamUrl = "https://example.test/existing.m3u8")
        val stale = Channel(name = "No longer in current catalog", streamUrl = "https://example.test/stale.m3u8")

        val result = PlayerLaunchRequestFactory.resolveCatalog(listOf(existing), stale)

        assertEquals(1, result.channelIndex)
        assertEquals(listOf(existing, stale), result.channels)
        assertSame(stale, result.channels.last())
    }

    @Test
    fun usesZeroIndexWhenLaunchingIntoEmptyCatalog() {
        val target = Channel(name = "Standalone", streamUrl = "https://example.test/standalone.m3u8")

        val result = PlayerLaunchRequestFactory.resolveCatalog(emptyList(), target)

        assertEquals(0, result.channelIndex)
        assertEquals(listOf(target), result.channels)
    }

    @Test
    fun choosesFirstEntryWhenCatalogContainsDuplicateIdentities() {
        val first = Channel(name = "Sports", streamUrl = "https://example.test/sports.m3u8")
        val duplicate = first.copy(name = "Sports alt")
        val result = PlayerLaunchRequestFactory.resolveCatalog(listOf(first, duplicate), duplicate)

        assertEquals(0, result.channelIndex)
        assertEquals(2, result.channels.size)
        assertSame(first, result.channels.first())
    }
}
