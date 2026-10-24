package com.angulismotv.player

/**
 * Coordinates a manual reload without owning playback engines or Android views.
 * The activity supplies the selected channel, lifecycle reset and renderer-specific actions.
 */
internal class PlaybackReloadController<T : Any>(
    private val selectedChannel: () -> T?,
    private val currentUrl: () -> String,
    private val currentType: () -> String,
    private val isHttpUrl: (String) -> Boolean,
    private val isIframeType: (String) -> Boolean,
    private val prepareForReload: () -> Unit,
    private val setCurrentStream: (String, String) -> Unit,
    private val reloadIframe: (String) -> Unit,
    private val reloadStream: (String, String) -> Unit,
    private val fallbackToFirstOption: (T) -> Unit,
    private val controlsVisible: () -> Boolean,
    private val resetAutoHideTimer: () -> Unit,
    private val showMissingChannelError: () -> Unit
) {
    fun reloadCurrentTransmission() {
        val channel = selectedChannel()
        if (channel == null) {
            showMissingChannelError()
            return
        }

        prepareForReload()
        val url = currentUrl()
        val type = currentType()
        if (url.isNotBlank() && isHttpUrl(url)) {
            setCurrentStream(url, type)
            if (isIframeType(type)) {
                reloadIframe(url)
            } else {
                reloadStream(url, type)
            }
        } else {
            fallbackToFirstOption(channel)
        }

        if (controlsVisible()) resetAutoHideTimer()
    }
}
