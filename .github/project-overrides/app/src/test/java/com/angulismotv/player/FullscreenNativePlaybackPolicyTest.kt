package com.angulismotv.player

import com.angulismotv.models.StreamType
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class FullscreenNativePlaybackPolicyTest {
    @Test
    fun allowsReuseForEnabledNativeSources() {
        listOf(StreamType.HLS, StreamType.DASH, StreamType.MP4).forEach { type ->
            assertTrue(
                "Debe permitir reutilizar una sesión nativa de tipo $type",
                FullscreenNativePlaybackPolicy.shouldReuseInlinePlayer(
                    enabled = true,
                    url = "https://example.test/live",
                    type = type
                )
            )
        }
    }

    @Test
    fun rejectsDisabledBlankAndIframeSessions() {
        assertFalse(
            FullscreenNativePlaybackPolicy.shouldReuseInlinePlayer(
                enabled = false,
                url = "https://example.test/live.m3u8",
                type = StreamType.HLS
            )
        )
        assertFalse(
            FullscreenNativePlaybackPolicy.shouldReuseInlinePlayer(
                enabled = true,
                url = " ",
                type = StreamType.HLS
            )
        )
        assertFalse(
            FullscreenNativePlaybackPolicy.shouldReuseInlinePlayer(
                enabled = true,
                url = "https://example.test/embed",
                type = StreamType.IFRAME
            )
        )
    }
}
