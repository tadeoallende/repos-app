package com.angulismotv.player

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class PlaybackLifecycleControllerTest {
    @Test
    fun resumeRestoresPreviouslyPlayingNativeSessionAndClearsFlag() {
        val harness = Harness(initiallyPlaying = true)
        harness.controller.onPauseBeforeSuper()
        assertTrue(harness.resumeAfterPause)
        harness.controller.onPauseAfterSuper()
        assertFalse(harness.playerWantsPlay)

        harness.calls.clear()
        harness.controller.onResume()

        assertEquals(
            listOf("orientation-resume", "immersive", "cast-start", "web-resume", "play"),
            harness.calls
        )
        assertTrue(harness.playerWantsPlay)
        assertFalse(harness.resumeAfterPause)
    }

    @Test
    fun deliberatePauseIsNotUndoneOnResume() {
        val harness = Harness(initiallyPlaying = false)
        harness.controller.onPauseBeforeSuper()
        harness.controller.onPauseAfterSuper()
        harness.calls.clear()

        harness.controller.onResume()

        assertFalse(harness.calls.contains("play"))
        assertFalse(harness.resumeAfterPause)
    }

    @Test
    fun finishingInlinePlayerReturnsSessionInsteadOfPausingIt() {
        val harness = Harness(
            initiallyPlaying = true,
            finishing = true,
            fromInline = true
        )

        harness.controller.onPauseBeforeSuper()
        harness.controller.onPauseAfterSuper()

        assertTrue(harness.calls.contains("return-inline"))
        assertFalse(harness.calls.contains("pause"))
        assertEquals(
            listOf("orientation-pause", "return-inline", "cast-stop", "web-pause"),
            harness.calls
        )
    }

    @Test
    fun stoppingActivityStopsWatchdogBeforePausingPlayer() {
        val harness = Harness(initiallyPlaying = true)

        harness.controller.onStopBeforeSuper()
        harness.controller.onStopAfterSuper()

        assertEquals(listOf("watchdog-stop", "pause"), harness.calls)
    }

    @Test
    fun stoppingFinishingFullscreenActivityDoesNotPauseReturnedInlineSession() {
        val harness = Harness(
            initiallyPlaying = true,
            finishing = true,
            fromInline = true
        )

        harness.controller.onStopBeforeSuper()
        harness.controller.onStopAfterSuper()

        assertEquals(listOf("watchdog-stop"), harness.calls)
        assertTrue(harness.playerWantsPlay)
    }

    private class Harness(
        initiallyPlaying: Boolean,
        private val finishing: Boolean = false,
        private val fromInline: Boolean = false
    ) {
        var playerWantsPlay = initiallyPlaying
        var resumeAfterPause = false
        private var zapping = false
        val calls = mutableListOf<String>()

        val controller = PlaybackLifecycleController(
            isTV = { false },
            isZapping = { zapping },
            isFinishing = { finishing },
            isFromInlinePlayer = { fromInline },
            resumeAfterPause = { resumeAfterPause },
            setResumeAfterPause = { resumeAfterPause = it },
            nativePlayerWantsPlay = { playerWantsPlay },
            playNativePlayer = {
                calls += "play"
                playerWantsPlay = true
            },
            pauseNativePlayer = {
                calls += "pause"
                playerWantsPlay = false
            },
            returnSessionToInline = { calls += "return-inline" },
            orientationOnResume = { calls += "orientation-resume" },
            orientationOnPause = { calls += "orientation-pause" },
            enableImmersiveFullscreen = { calls += "immersive" },
            startCastDiscovery = { calls += "cast-start" },
            stopCastDiscovery = { calls += "cast-stop" },
            resumeWebView = { calls += "web-resume" },
            pauseWebView = { calls += "web-pause" },
            stopRecoveryWatchdog = { calls += "watchdog-stop" }
        )
    }
}
