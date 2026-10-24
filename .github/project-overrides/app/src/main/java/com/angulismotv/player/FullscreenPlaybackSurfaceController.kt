package com.angulismotv.player

import android.view.View
import android.webkit.WebView
import android.widget.ProgressBar
import android.widget.TextView

/**
 * Coordinates the view transition from iframe playback to native fullscreen playback.
 * It does not own the player or recovery policy; those remain delegated to their controllers.
 */
internal class FullscreenPlaybackSurfaceController(
    private val playerTimelineContainer: View,
    private val playerView: View,
    private val webView: WebView,
    private val webViewTouchBlocker: View,
    private val progressBar: ProgressBar,
    private val errorText: TextView,
    private val isTV: () -> Boolean,
    private val stopTimelineUpdates: () -> Unit,
    private val invalidatePendingWebLoad: () -> Unit,
    private val stopRecoveryWatchdog: () -> Unit,
    private val releasePlayer: () -> Unit,
    private val stopWebBridgeMonitor: () -> Unit,
    private val detachWebBridge: () -> Unit,
    private val setCurrentIsLive: (Boolean) -> Unit,
    private val setStreamIsLive: (Boolean) -> Unit,
    private val setCurrentStreamType: (String) -> Unit,
    private val currentGeneration: () -> Int,
    private val lockWebViewFocus: () -> Unit
) {
    fun prepareNativePlaybackSurface(type: String): Int {
        playerTimelineContainer.visibility = View.GONE
        stopTimelineUpdates()
        invalidatePendingWebLoad()
        stopRecoveryWatchdog()
        releasePlayer()

        val hadVisibleWebView = webView.visibility == View.VISIBLE
        playerView.visibility = View.VISIBLE
        webView.visibility = View.GONE
        webViewTouchBlocker.visibility = View.GONE
        progressBar.visibility = View.VISIBLE
        errorText.visibility = View.GONE
        setCurrentIsLive(false)
        setStreamIsLive(false)
        if (hadVisibleWebView) {
            // Stop an old iframe before switching surfaces to prevent background audio.
            stopWebBridgeMonitor()
            detachWebBridge()
            webView.stopLoading()
            webView.loadUrl("about:blank")
        }
        setCurrentStreamType(type)
        configureNativePlayerFocus()
        return currentGeneration()
    }

    fun configureNativePlayerFocus() {
        if (!FullscreenPlaybackSurfacePolicy.shouldRequestNativeFocus(isTV())) return
        playerView.isFocusable = true
        playerView.isFocusableInTouchMode = true
        playerView.requestFocus()
        lockWebViewFocus()
    }
}

/** Small pure policy to make device-specific focus behavior easy to verify. */
internal object FullscreenPlaybackSurfacePolicy {
    fun shouldRequestNativeFocus(isTV: Boolean): Boolean = isTV
}
