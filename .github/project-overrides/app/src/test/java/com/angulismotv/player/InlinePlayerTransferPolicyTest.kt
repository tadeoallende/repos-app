package com.angulismotv.player

import com.angulismotv.models.StreamType
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class InlinePlayerTransferPolicyTest {
    @Test
    fun transfersNativeStreamOnlyWhenLaunchingFromInline() {
        val plan = resolve(
            fromInline = true,
            nativePlayerAvailable = true,
            streamUrl = "https://example.test/live.m3u8",
            streamType = StreamType.HLS
        )
        assertEquals(InlinePlayerTransferMode.NATIVE_PLAYER, plan.mode)
        assertTrue(plan.transferNativePlayer)
        assertFalse(plan.transferWebView)
    }

    @Test
    fun transfersLoadedIframeOnlyWhenThereIsNoNativePlayer() {
        val plan = resolve(
            fromInline = true,
            nativePlayerAvailable = false,
            streamUrl = "https://example.test/embed",
            streamType = StreamType.IFRAME,
            webViewVisible = true,
            webViewHasUrl = true
        )
        assertEquals(InlinePlayerTransferMode.WEB_VIEW, plan.mode)
        assertFalse(plan.transferNativePlayer)
        assertTrue(plan.transferWebView)
    }

    @Test
    fun doesNotTransferIframeWhenWebViewIsHiddenOrHasNoUrl() {
        val hidden = resolve(
            fromInline = true,
            nativePlayerAvailable = false,
            streamUrl = "https://example.test/embed",
            streamType = StreamType.IFRAME,
            webViewVisible = false,
            webViewHasUrl = true
        )
        val missingUrl = resolve(
            fromInline = true,
            nativePlayerAvailable = false,
            streamUrl = "https://example.test/embed",
            streamType = StreamType.IFRAME,
            webViewVisible = true,
            webViewHasUrl = false
        )
        assertEquals(InlinePlayerTransferMode.NONE, hidden.mode)
        assertEquals(InlinePlayerTransferMode.NONE, missingUrl.mode)
        assertFalse(hidden.transferWebView)
        assertFalse(missingUrl.transferWebView)
    }

    @Test
    fun doesNotTransferWhenLaunchIsNotFromInline() {
        val plan = resolve(
            fromInline = false,
            nativePlayerAvailable = true,
            streamUrl = "https://example.test/live.m3u8",
            streamType = StreamType.HLS,
            webViewVisible = true,
            webViewHasUrl = true
        )
        assertEquals(InlinePlayerTransferMode.NONE, plan.mode)
        assertFalse(plan.transferNativePlayer)
        assertFalse(plan.transferWebView)
    }

    @Test
    fun blankUrlNeverTransfersAndIframeDoesNotTransferAsNativePlayer() {
        val blank = resolve(
            fromInline = true,
            nativePlayerAvailable = true,
            streamUrl = " ",
            streamType = StreamType.HLS
        )
        val iframeWithNativePlayer = resolve(
            fromInline = true,
            nativePlayerAvailable = true,
            streamUrl = "https://example.test/embed",
            streamType = StreamType.IFRAME,
            webViewVisible = true,
            webViewHasUrl = true
        )
        assertEquals(InlinePlayerTransferMode.NONE, blank.mode)
        assertEquals(InlinePlayerTransferMode.NONE, iframeWithNativePlayer.mode)
        assertFalse(blank.transferNativePlayer)
        assertFalse(blank.transferWebView)
        assertFalse(iframeWithNativePlayer.transferNativePlayer)
        assertFalse(iframeWithNativePlayer.transferWebView)
    }

    private fun resolve(
        fromInline: Boolean,
        nativePlayerAvailable: Boolean,
        streamUrl: String,
        streamType: String,
        webViewVisible: Boolean = false,
        webViewHasUrl: Boolean = false
    ) = InlinePlayerTransferPolicy.resolve(
        fromInline = fromInline,
        nativePlayerAvailable = nativePlayerAvailable,
        streamUrl = streamUrl,
        streamType = streamType,
        webViewVisible = webViewVisible,
        webViewHasUrl = webViewHasUrl
    )
}
