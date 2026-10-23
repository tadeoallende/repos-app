package com.angulismotv.player

import android.content.Context
import android.content.Intent
import com.angulismotv.UnifiedPlayerActivity
import com.angulismotv.models.Channel
import com.angulismotv.models.ChannelIdentity
import com.angulismotv.models.StreamType

/**
 * Prepara el catálogo e Intent de pantalla completa sin mezclar esas tareas con la UI de canales.
 * La identidad se basa en ChannelIdentity y los canales obsoletos se conservan al final del catálogo.
 */
internal data class PlayerLaunchCatalog(
    val channels: List<Channel>,
    val channelIndex: Int
)

internal object PlayerLaunchRequestFactory {

    fun resolveCatalog(originalChannels: List<Channel>, channel: Channel): PlayerLaunchCatalog {
        val matchingIndex = originalChannels.indexOfFirst { ChannelIdentity.same(it, channel) }
        // Un canal desactualizado se agrega al final; nunca se reemplaza por el primer canal.
        val channels = if (matchingIndex >= 0) originalChannels else originalChannels + channel
        val index = if (matchingIndex >= 0) matchingIndex else channels.lastIndex
        return PlayerLaunchCatalog(channels, index)
    }

    fun createIntent(
        context: Context,
        channel: Channel,
        catalog: PlayerLaunchCatalog,
        catalogToken: Long,
        fromInline: Boolean,
        isTV: Boolean,
        sourceIndex: Int,
        handoff: InlinePlayerTransferPlan,
        openChannelPanel: Boolean = false,
        openChannelSearch: Boolean = false
    ): Intent = Intent(context, UnifiedPlayerActivity::class.java).apply {
        // Evitar incluir el catálogo entero en el Intent: los bundles tienen límite de tamaño.
        putExtra("channel_catalog_token", catalogToken)
        putExtra("current_channel", channel)
        putExtra("channel_index", catalog.channelIndex)
        putExtra("channel_name", channel.name)
        putExtra("channel_logo", channel.logo)
        putExtra("stream_url", channel.streamUrl)
        putExtra("stream_type", channel.streamType ?: StreamType.AUTO)
        putExtra("from_inline_player", fromInline)
        putExtra("force_landscape_fullscreen", fromInline && !isTV)
        putExtra("source_index", sourceIndex)
        putExtra("reuse_inline_player_session", handoff.transferNativePlayer)
        putExtra("reuse_inline_webview_session", handoff.transferWebView)
        putExtra("open_channel_panel", openChannelPanel)
        putExtra("open_channel_search", openChannelSearch)
    }
}
