package com.angulismotv.player

import com.angulismotv.models.Channel
import com.angulismotv.models.StreamOption
import com.angulismotv.models.StreamType
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class InlinePlaybackSourceResolverTest {
    @Test
    fun resolvesTheRequestedAlternativeWithoutChangingItsIndex() {
        val channel = Channel(
            name = "Canal",
            options = listOf(
                StreamOption(name = "Primera", iframe = "https://one.example/live.m3u8", streamType = StreamType.AUTO),
                StreamOption(name = "Segunda", iframe = "https://two.example/player", streamType = StreamType.IFRAME)
            )
        )
        assertEquals(
            InlinePlaybackSource("https://two.example/player", StreamType.IFRAME),
            InlinePlaybackSourceResolver.resolve(channel, 1)
        )
    }

    @Test
    fun invalidAlternativeIndexReturnsNoSourceInsteadOfPickingAnotherOption() {
        val channel = Channel(
            name = "Canal",
            options = listOf(StreamOption(name = "Primera", iframe = "https://one.example/live.m3u8"))
        )
        assertNull(InlinePlaybackSourceResolver.resolve(channel, 5))
    }

    @Test
    fun resolvesDirectStreamWhenNoAlternativesExist() {
        val channel = Channel(
            name = "Canal",
            streamUrl = "https://example.com/live.m3u8",
            streamType = StreamType.AUTO,
            options = emptyList()
        )
        assertEquals(
            InlinePlaybackSource("https://example.com/live.m3u8", StreamType.HLS),
            InlinePlaybackSourceResolver.resolve(channel, 0)
        )
    }

    @Test
    fun keepsAnEmptyDirectStreamEmptyForTheCallerToHandle() {
        val channel = Channel(name = "Canal", streamUrl = "", streamType = StreamType.AUTO)
        assertEquals(
            InlinePlaybackSource("", StreamType.AUTO),
            InlinePlaybackSourceResolver.resolve(channel, 0)
        )
    }
}
