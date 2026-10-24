package com.angulismotv.player

import android.view.View
import android.view.ViewGroup
import android.webkit.WebView
import com.angulismotv.models.Channel
import com.angulismotv.models.StreamType
import com.google.android.exoplayer2.ExoPlayer

/**
 * Describes which inline engine, if any, can be reused on the fullscreen screen.
 */
internal enum class InlinePlayerTransferMode {
    NONE,
    NATIVE_PLAYER,
    WEB_VIEW
}

/**
 * A transfer has exactly one owner: the existing native player, the existing WebView, or neither.
 * Computed flags preserve the small API already used by launch-intent construction.
 */
internal data class InlinePlayerTransferPlan(
    val mode: InlinePlayerTransferMode
) {
    val transferNativePlayer: Boolean
        get() = mode == InlinePlayerTransferMode.NATIVE_PLAYER

    val transferWebView: Boolean
        get() = mode == InlinePlayerTransferMode.WEB_VIEW

    companion object {
        val NONE = InlinePlayerTransferPlan(InlinePlayerTransferMode.NONE)
        val NATIVE_PLAYER = InlinePlayerTransferPlan(InlinePlayerTransferMode.NATIVE_PLAYER)
        val WEB_VIEW = InlinePlayerTransferPlan(InlinePlayerTransferMode.WEB_VIEW)
    }
}

/** Pure eligibility policy so transfer decisions can be unit-tested without Android views. */
internal object InlinePlayerTransferPolicy {
    fun resolve(
        fromInline: Boolean,
        nativePlayerAvailable: Boolean,
        streamUrl: String,
        streamType: String,
        webViewVisible: Boolean,
        webViewHasUrl: Boolean
    ): InlinePlayerTransferPlan {
        if (!fromInline || streamUrl.isBlank()) return InlinePlayerTransferPlan.NONE

        return if (streamType.equals(StreamType.IFRAME, ignoreCase = true)) {
            if (!nativePlayerAvailable && webViewVisible && webViewHasUrl) {
                InlinePlayerTransferPlan.WEB_VIEW
            } else {
                InlinePlayerTransferPlan.NONE
            }
        } else if (nativePlayerAvailable) {
            InlinePlayerTransferPlan.NATIVE_PLAYER
        } else {
            InlinePlayerTransferPlan.NONE
        }
    }
}

/**
 * Owns transfer preparation only. The existing InlinePlayerHandoff object keeps session ownership,
 * while ChannelsFragment remains responsible for starting the destination Activity and recovery.
 */
internal class InlinePlayerTransferController(
    private val playerProvider: () -> ExoPlayer?,
    private val streamUrlProvider: () -> String,
    private val streamTypeProvider: () -> String,
    private val sourceIndexProvider: () -> Int,
    private val channelProvider: () -> Channel?,
    private val webView: WebView,
    private val recoveryProvider: () -> PlaybackRecoveryController?,
    private val playbackEngineProvider: () -> InlinePlaybackEngineController?,
    private val setLaunchingFullscreen: (Boolean) -> Unit
) {
    fun prepare(channel: Channel, fromInline: Boolean): InlinePlayerTransferPlan {
        setLaunchingFullscreen(fromInline)
        recoveryProvider()?.apply {
            stopWatchdog()
            cancelStablePlaybackTimer()
            cancelPendingReconnect()
        }

        val player = playerProvider()
        val streamUrl = streamUrlProvider()
        val streamType = streamTypeProvider()
        val plan = InlinePlayerTransferPolicy.resolve(
            fromInline = fromInline,
            nativePlayerAvailable = player != null,
            streamUrl = streamUrl,
            streamType = streamType,
            webViewVisible = webView.visibility == View.VISIBLE,
            webViewHasUrl = webView.url != null
        )

        when (plan.mode) {
            InlinePlayerTransferMode.NATIVE_PLAYER -> {
                // La política solo devuelve este modo cuando hay reproductor nativo disponible.
                if (player != null) {
                    offerNativePlayerToFullscreen(channel, player, streamUrl, streamType)
                } else {
                    player?.pause()
                }
            }
            InlinePlayerTransferMode.WEB_VIEW -> offerWebViewToFullscreen(channel, streamUrl)
            InlinePlayerTransferMode.NONE -> player?.pause()
        }
        webView.onPause()
        return plan
    }

    private fun offerNativePlayerToFullscreen(
        channel: Channel,
        player: ExoPlayer,
        streamUrl: String,
        streamType: String
    ) {
        val session = InlinePlayerHandoff.Session(
            player = player,
            channel = channelProvider() ?: channel,
            streamUrl = streamUrl,
            streamType = streamType,
            sourceIndex = sourceIndexProvider(),
            wasPlaying = player.playWhenReady
        )
        playbackEngineProvider()?.detachForHandoff(player)
        InlinePlayerHandoff.offerToFullscreen(session)
    }

    private fun offerWebViewToFullscreen(channel: Channel, streamUrl: String) {
        val oldParent = webView.parent as? ViewGroup
        val oldIndex = oldParent?.indexOfChild(webView) ?: -1
        val oldParams = webView.layoutParams
        // Re-parent the current iframe page rather than triggering a second load.
        oldParent?.removeView(webView)
        InlinePlayerHandoff.offerToFullscreen(
            InlinePlayerHandoff.Session(
                player = null,
                channel = channelProvider() ?: channel,
                streamUrl = streamUrl,
                streamType = StreamType.IFRAME,
                sourceIndex = sourceIndexProvider(),
                wasPlaying = true,
                webView = webView,
                webViewParentIndex = oldIndex,
                webViewLayoutParams = oldParams
            )
        )
    }
}
