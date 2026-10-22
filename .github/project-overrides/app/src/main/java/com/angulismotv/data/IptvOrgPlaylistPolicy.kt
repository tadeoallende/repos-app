package com.angulismotv.data

import java.net.URI

/** Resolves IPTV-org URLs to the metadata-rich global index before regional filtering. */
internal object IptvOrgPlaylistPolicy {
    const val DEFAULT_PLAYLIST_URL = "https://iptv-org.github.io/iptv/index.m3u"
    private const val OFFICIAL_HOST = "iptv-org.github.io"
    private const val OFFICIAL_PATH_PREFIX = "/iptv/"

    fun resolve(configuredUrl: String?): String {
        val value = configuredUrl?.trim().orEmpty()
        if (value.equals("disabled", ignoreCase = true)) return ""
        if (value.isBlank()) return DEFAULT_PLAYLIST_URL

        val uri = runCatching { URI(value) }.getOrNull()
        val isOfficialPlaylist = uri?.host?.equals(OFFICIAL_HOST, ignoreCase = true) == true &&
            uri.path.orEmpty().startsWith(OFFICIAL_PATH_PREFIX, ignoreCase = true)
        return if (isOfficialPlaylist) DEFAULT_PLAYLIST_URL else value
    }

    /** Custom M3U URLs are left alone and are not subject to the IPTV-org regional filter. */
    fun shouldApplyAmericasFilter(configuredUrl: String?): Boolean {
        val resolved = resolve(configuredUrl)
        val uri = runCatching { URI(resolved) }.getOrNull() ?: return false
        return uri.host?.equals(OFFICIAL_HOST, ignoreCase = true) == true &&
            uri.path.orEmpty().startsWith(OFFICIAL_PATH_PREFIX, ignoreCase = true)
    }
}
