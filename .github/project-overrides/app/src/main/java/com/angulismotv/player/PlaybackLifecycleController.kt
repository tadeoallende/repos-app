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
    /**
     * onStop normally follows onPause. Remember whether onPause already paused the native player
     * so onStop only performs the fallback pause if onPause intentionally skipped it (for example,
     * while zapping) or was not routed through this controller.
     */
    private var nativePauseHandledSinceResume = false

    /** Called by Activity.onResume() immediately after super.onResume(). */
    fun onResume() {
        nativePauseHandledSinceResume = false
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
            // The session now belongs to the inline screen; never pause it from onStop.
            nativePauseHandledSinceResume = true
        } else if (!isZapping()) {
            pauseNativePlayer()
            nativePauseHandledSinceResume = true
        } else {
            // If the Activity is actually stopped during a zap, onStop is still the safe fallback.
            nativePauseHandledSinceResume = false
        }
        stopCastDiscovery()
        pauseWebView()
    }

    /** Called before super.onStop() so the watchdog cannot poll a hidden Activity. */
    fun onStopBeforeSuper() {
        stopRecoveryWatchdog()
    }

    /**
     * onPause usually has already paused the engine. Avoid a second pause call, but retain the
     * fallback for unusual lifecycle paths and for a zap interrupted by an Activity stop.
     */
    fun onStopAfterSuper() {
        if (isFinishing() && isFromInlinePlayer()) return
        if (!nativePauseHandledSinceResume) {
            pauseNativePlayer()
            nativePauseHandledSinceResume = true
        }
    }
}
