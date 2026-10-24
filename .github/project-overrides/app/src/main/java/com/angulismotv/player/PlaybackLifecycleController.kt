package com.angulismotv.player

/**
 * Coordinates playback-related Activity lifecycle transitions through callbacks.
 * Android super calls stay in the Activity, so their ordering remains explicit.
 */
internal class PlaybackLifecycleController(
    private val isTV: () -> Boolean,
    private val isZapping: () -> Boolean,
    private val isFinishing: () -> Boolean,
    private val isFromInlinePlayer: () -> Boolean,
    private val resumeAfterPause: () -> Boolean,
    private val setResumeAfterPause: (Boolean) -> Unit,
    private val nativePlayerWantsPlay: () -> Boolean,
    private val playNativePlayer: () -> Unit,
    private val pauseNativePlayer: () -> Unit,
    private val returnSessionToInline: () -> Unit,
    private val orientationOnResume: () -> Unit,
    private val orientationOnPause: () -> Unit,
    private val enableImmersiveFullscreen: () -> Unit,
    private val startCastDiscovery: () -> Unit,
    private val stopCastDiscovery: () -> Unit,
    private val resumeWebView: () -> Unit,
    private val pauseWebView: () -> Unit,
    private val stopRecoveryWatchdog: () -> Unit
) {
    /** Called by Activity.onResume() immediately after super.onResume(). */
    fun onResume() {
        orientationOnResume()
        if (!isTV()) enableImmersiveFullscreen()
        startCastDiscovery()
        resumeWebView()
        if (resumeAfterPause() && !isZapping()) playNativePlayer()
        setResumeAfterPause(false)
    }

    /** Called before super.onPause() to capture the user's play/pause intent. */
    fun onPauseBeforeSuper() {
        orientationOnPause()
        setResumeAfterPause(!isZapping() && nativePlayerWantsPlay())
    }

    /** Called after super.onPause(), preserving inline handoff before pausing the engine. */
    fun onPauseAfterSuper() {
        if (isFinishing() && isFromInlinePlayer()) {
            returnSessionToInline()
        } else if (!isZapping()) {
            pauseNativePlayer()
        }
        stopCastDiscovery()
        pauseWebView()
    }

    /** Called before super.onStop() so the watchdog cannot poll a hidden Activity. */
    fun onStopBeforeSuper() {
        stopRecoveryWatchdog()
    }

    /** Called after super.onStop(), matching the existing behavior of pausing the engine. */
    fun onStopAfterSuper() {
        pauseNativePlayer()
    }
}
