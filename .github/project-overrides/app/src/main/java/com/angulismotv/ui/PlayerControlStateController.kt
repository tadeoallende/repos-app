package com.angulismotv.ui

import android.view.View
import android.widget.ImageButton
import com.angulismotv.models.StreamType

/**
 * Projects the current playback mode into the fullscreen player's control visibility and focus.
 *
 * The Activity remains the owner of playback/session state and supplies it through callbacks.
 */
class PlayerControlStateController(
    private val isTv: () -> Boolean,
    private val streamType: () -> String,
    private val castConfigured: () -> Boolean,
    private val hasMultipleOptions: () -> Boolean,
    private val currentIsLive: () -> Boolean,
    private val streamIsLive: () -> Boolean,
    private val iframeIsControllable: () -> Boolean,
    private val iframeIsPlaying: () -> Boolean,
    private val iframeDurationMs: () -> Long,
    private val menuButton: ImageButton,
    private val playPauseButton: ImageButton,
    private val rewindButton: ImageButton,
    private val forwardButton: ImageButton,
    private val optionsButton: ImageButton,
    private val reloadButton: ImageButton,
    private val closeButton: ImageButton,
    private val castButton: ImageButton,
    private val onPlayStateChanged: (Boolean) -> Unit,
    private val updateControlFocusOrder: () -> Unit
) {

    fun updateControlsVisibility() {
        updateCastButtonVisibility()
        updateTransportControlsVisibility()
        optionsButton.visibility = if (hasMultipleOptions()) View.VISIBLE else View.GONE
        if (isTv()) configureTvControlFocusOrder()
    }

    fun updateCastButtonVisibility() {
        castButton.visibility = if (
            !isTv() && streamType() != StreamType.IFRAME && castConfigured()
        ) View.VISIBLE else View.GONE
    }

    fun updateTransportControlsVisibility() {
        when (streamType()) {
            StreamType.IFRAME -> updateIframeTransportControls()
            else -> updateNativeTransportControls()
        }
    }

    fun updateIframeTransportControls() {
        if (!isTv()) {
            // On phones, embedded providers own their own touch controls.
            playPauseButton.visibility = View.GONE
            rewindButton.visibility = View.GONE
            forwardButton.visibility = View.GONE
            return
        }

        if (iframeIsControllable()) {
            playPauseButton.visibility = View.VISIBLE
            onPlayStateChanged(iframeIsPlaying())
            val showSeek = iframeDurationMs() > 0L
            rewindButton.visibility = if (showSeek) View.VISIBLE else View.GONE
            forwardButton.visibility = if (showSeek) View.VISIBLE else View.GONE
            playPauseButton.isFocusable = true
            rewindButton.isFocusable = showSeek
            forwardButton.isFocusable = showSeek
        } else {
            playPauseButton.visibility = View.GONE
            rewindButton.visibility = View.GONE
            forwardButton.visibility = View.GONE
        }
    }

    fun updateNativeTransportControls() {
        playPauseButton.visibility = View.VISIBLE
        val showSeek = !currentIsLive() && !streamIsLive()
        rewindButton.visibility = if (showSeek) View.VISIBLE else View.GONE
        forwardButton.visibility = if (showSeek) View.VISIBLE else View.GONE
    }

    fun configureTvControlFocusOrder() {
        menuButton.visibility = View.VISIBLE
        menuButton.isFocusable = true
        listOf(playPauseButton, rewindButton, forwardButton, optionsButton, reloadButton).forEach {
            it.isFocusable = it.visibility == View.VISIBLE
        }
        closeButton.isFocusable = true
        castButton.isFocusable = castButton.visibility == View.VISIBLE
        updateControlFocusOrder()
    }
}
