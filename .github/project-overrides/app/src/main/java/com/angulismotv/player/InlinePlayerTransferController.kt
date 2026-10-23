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
internal data class InlinePlayerTransferPlan(
    val transferNativePlayer: Boolean,
    val transferWebView: Boolean
) {
    companion object {
        val NONE = InlinePlayerTransferPlan(false, false)
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
        val transferNativePlayer = fromInline &&
            nativePlayerAvailable &&
            streamUrl.isNotBlank() &&
            streamType != StreamType.IFRAME

        val transferWebView = fromInline &&
            !nativePlayerAvailable &&
            streamType == StreamType.IFRAME &&
            streamUrl.isNotBlank() &&
            webViewVisible &&
            webViewHasUrl

        return InlinePlayerTransferPlan(transferNativePlayer, transferWebView)
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

        when {
            plan.transferNativePlayer && player != null ->
                offerNativePlayerToFullscreen(channel, player, streamUrl, streamType)
            plan.transferWebView -> offerWebViewToFullscreen(channel, streamUrl)
            else -> player?.pause()
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
