package com.angulismotv.player

import android.content.Context
import com.angulismotv.models.StreamType
import com.google.android.exoplayer2.DefaultRenderersFactory
import com.google.android.exoplayer2.ExoPlayer
import com.google.android.exoplayer2.ui.PlayerView

/**
 * Owns native fullscreen player creation and the reuse of an inline native session.
 *
 * WebView/iframe playback remains under WebViewPlaybackController. Reusing an inline player
 * deliberately avoids replacing its media source or calling prepare(), preserving buffer and
 * playback position while moving the same engine into the fullscreen PlayerView.
 */
internal class FullscreenNativePlaybackController(
    private val context: Context,
    private val playerView: PlayerView,
    private val playerEvents: FullscreenPlayerEventController,
    private val setCurrentPlayer: (ExoPlayer) -> Unit,
    private val onPlayStateChanged: (Boolean) -> Unit
) {
    fun reuseInlinePlayerIfAvailable(
        enabled: Boolean,
        url: String,
        type: String,
        generation: Int
    ): Boolean {
        if (!FullscreenNativePlaybackPolicy.shouldReuseInlinePlayer(enabled, url, type)) {
            return false
        }

        val handoff = InlinePlayerHandoff.takeForFullscreen(url, type) ?: return false
        val player = handoff.player ?: return false

        setCurrentPlayer(player)
        playerView.player = player
        playerView.useController = false
        playerEvents.attach(player, url, type, generation)

        // Do not replace media or call prepare(): retain the existing buffer and position.
        player.playWhenReady = handoff.wasPlaying
        onPlayStateChanged(player.isPlaying)
        playerEvents.handleCurrentState(player, url, type, generation, player.playbackState)
        return true
    }

    fun createAndStart(
        url: String,
        type: String,
        generation: Int,
        playWhenReady: Boolean
    ) {
        val mediaSource = StreamMediaSourceFactory.create(url, type)

        // Some Android TV devices expose multiple decoders for the same audio format.
        // Allow ExoPlayer to fall back if its preferred decoder fails to initialize.
        val renderersFactory = DefaultRenderersFactory(context)
            .setEnableDecoderFallback(true)
        val player = ExoPlayer.Builder(context, renderersFactory)
            .setLoadControl(
                StreamMediaSourceFactory.createLoadControl(
                    StreamMediaSourceFactory.BufferProfile.FULLSCREEN
                )
            )
            .build()

        setCurrentPlayer(player)
        playerView.player = player
        playerView.useController = false
        playerEvents.attach(player, url, type, generation)
        player.setMediaSource(mediaSource)
        player.playWhenReady = playWhenReady
        player.prepare()
    }
}

/** Keeps iframe pages out of the native-player reuse path. */
internal object FullscreenNativePlaybackPolicy {
    fun shouldReuseInlinePlayer(enabled: Boolean, url: String, type: String): Boolean =
        enabled && url.isNotBlank() &&
            !type.equals(StreamType.IFRAME, ignoreCase = true)
}
