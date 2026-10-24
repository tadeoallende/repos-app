package com.angulismotv.player

import org.junit.Assert.assertEquals
import org.junit.Test

class PlaybackReloadControllerTest {
    @Test
    fun missingChannelShowsErrorWithoutChangingPlayback() {
        val calls = mutableListOf<String>()
        controller(channel = null, calls = calls).reloadCurrentTransmission()
        assertEquals(listOf("missing-channel"), calls)
    }

    @Test
    fun iframeReloadForcesFreshNavigationAndResetsControlsTimer() {
        val calls = mutableListOf<String>()
        controller(channel = "selected-channel", calls = calls).reloadCurrentTransmission()
        assertEquals(
            listOf(
                "prepare",
                "set:https://example.test/embed:iframe",
                "iframe:https://example.test/embed",
                "auto-hide"
            ),
            calls
        )
    }

    @Test
    fun nativeStreamReloadUsesExistingStreamRoute() {
        val calls = mutableListOf<String>()
        controller(
            channel = "selected-channel",
            calls = calls,
            url = "https://example.test/live.m3u8",
            type = "hls"
        ).reloadCurrentTransmission()
        assertEquals(
            listOf(
                "prepare",
                "set:https://example.test/live.m3u8:hls",
                "stream:https://example.test/live.m3u8:hls",
                "auto-hide"
            ),
            calls
        )
    }

    @Test
    fun invalidCurrentUrlFallsBackToSelectedChannelOptions() {
        val calls = mutableListOf<String>()
        controller(
            channel = "selected-channel",
            calls = calls,
            url = "not-a-url",
            controls = false
        ).reloadCurrentTransmission()
        assertEquals(listOf("prepare", "fallback:selected-channel"), calls)
    }

    private fun controller(
        channel: String?,
        calls: MutableList<String>,
        url: String = "https://example.test/embed",
        type: String = "iframe",
        controls: Boolean = true
    ) = PlaybackReloadController(
        selectedChannel = { channel },
        currentUrl = { url },
        currentType = { type },
        isHttpUrl = { it.startsWith("https://") || it.startsWith("http://") },
        isIframeType = { it.equals("iframe", ignoreCase = true) },
        prepareForReload = { calls += "prepare" },
        setCurrentStream = { nextUrl, nextType -> calls += "set:$nextUrl:$nextType" },
        reloadIframe = { nextUrl -> calls += "iframe:$nextUrl" },
        reloadStream = { nextUrl, nextType -> calls += "stream:$nextUrl:$nextType" },
        fallbackToFirstOption = { selected -> calls += "fallback:$selected" },
        controlsVisible = { controls },
        resetAutoHideTimer = { calls += "auto-hide" },
        showMissingChannelError = { calls += "missing-channel" }
    )
}
