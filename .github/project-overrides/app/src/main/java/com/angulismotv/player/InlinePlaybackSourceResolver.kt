package com.angulismotv.player

import com.angulismotv.models.Channel
import com.angulismotv.models.StreamType

/** A resolved source selected by the caller; this class never advances to another option. */
internal data class InlinePlaybackSource(
    val url: String,
    val type: String
)

/**
 * Resolves only the requested channel source. UI error messages and retry behavior remain
 * in ChannelsFragment so changing a source stays an explicit user action.
 */
internal object InlinePlaybackSourceResolver {
    fun resolve(channel: Channel, sourceIndex: Int): InlinePlaybackSource? {
        val options = channel.options.orEmpty()
        if (options.isNotEmpty()) {
            if (sourceIndex !in options.indices) return null
            val option = options[sourceIndex]
            return InlinePlaybackSource(
                url = option.iframe,
                type = StreamUtils.resolveType(option.iframe, option.streamType)
            )
        }

        val url = channel.streamUrl.orEmpty()
        return InlinePlaybackSource(
            url = url,
            type = StreamUtils.resolveType(url, channel.streamType ?: StreamType.AUTO)
        )
    }
}
