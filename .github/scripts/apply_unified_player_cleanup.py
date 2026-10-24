#!/usr/bin/env python3
"""Remove dead UnifiedPlayerActivity code and centralize last-channel persistence."""
from pathlib import Path
import re
import sys

A = "app/src/main/java/com/angulismotv/UnifiedPlayerActivity.kt"
F = "app/src/main/java/com/angulismotv/fragments/ChannelsFragment.kt"
L = "app/src/main/res/layout/activity_unified_player.xml"
D = "app/src/main/res/values/dimens.xml"
S = "app/src/main/java/com/angulismotv/data/LastPlayedChannelStore.kt"
T = "app/src/test/java/com/angulismotv/data/LastPlayedChannelResolverTest.kt"

STORE = """package com.angulismotv.data

import android.content.Context
import com.angulismotv.models.Channel
import com.angulismotv.models.ChannelIdentity

/** Owns the persistent snapshot used to restore the last active channel on Android TV. */
class LastPlayedChannelStore(context: Context) {
    private val preferences = context.applicationContext.getSharedPreferences(
        PREFERENCES_NAME,
        Context.MODE_PRIVATE
    )

    fun remember(channel: Channel) {
        preferences.edit()
            .putString(KEY_CHANNEL_ID, ChannelIdentity.key(channel))
            .putString(KEY_CHANNEL_NAME, channel.name)
            .putString(KEY_CHANNEL_LOGO, channel.logo)
            .apply()
    }

    fun resolve(channels: List<Channel>): Channel? = LastPlayedChannelResolver.resolve(
        channels = channels,
        savedKey = preferences.getString(KEY_CHANNEL_ID, null),
        savedName = preferences.getString(KEY_CHANNEL_NAME, null).orEmpty(),
        savedLogo = preferences.getString(KEY_CHANNEL_LOGO, null)
    )

    /** Remove only this feature's keys, leaving unrelated preferences intact. */
    fun clear() {
        preferences.edit()
            .remove(KEY_CHANNEL_ID)
            .remove(KEY_CHANNEL_NAME)
            .remove(KEY_CHANNEL_LOGO)
            .apply()
    }

    private companion object {
        const val PREFERENCES_NAME = "angulismotv_playback"
        const val KEY_CHANNEL_ID = "last_channel_key"
        const val KEY_CHANNEL_NAME = "last_channel_name"
        const val KEY_CHANNEL_LOGO = "last_channel_logo"
    }
}

/** Pure matching policy, separated so last-channel restoration can be unit-tested. */
internal object LastPlayedChannelResolver {
    fun resolve(channels: List<Channel>, savedKey: String?, savedName: String, savedLogo: String?): Channel? {
        if (channels.isEmpty()) return null
        return channels.firstOrNull {
            !savedKey.isNullOrBlank() && ChannelIdentity.key(it) == savedKey
        } ?: channels.firstOrNull {
            savedName.isNotBlank() && it.name.equals(savedName, ignoreCase = true) &&
                (savedLogo.isNullOrBlank() || it.logo == savedLogo)
        } ?: channels.firstOrNull {
            savedName.isNotBlank() && it.name.equals(savedName, ignoreCase = true)
        }
    }
}
"""

TEST = """package com.angulismotv.data

import com.angulismotv.models.Channel
import com.angulismotv.models.ChannelIdentity
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class LastPlayedChannelResolverTest {
    private val sports = Channel(name = "Sports", logo = "sports.png", category = "Deportes")
    private val news = Channel(name = "News", logo = "news.png", category = "Noticias")
    private val channels = listOf(sports, news)

    @Test
    fun prefersStableIdentityWhenItMatches() {
        assertEquals(news, LastPlayedChannelResolver.resolve(channels, ChannelIdentity.key(news), "Sports", "sports.png"))
    }

    @Test
    fun fallsBackToCaseInsensitiveNameAndMatchingLogo() {
        assertEquals(news, LastPlayedChannelResolver.resolve(channels, "removed-key", "nEwS", "news.png"))
    }

    @Test
    fun fallsBackToCaseInsensitiveNameWhenLogoChanged() {
        assertEquals(news, LastPlayedChannelResolver.resolve(channels, null, "NEWS", "old-logo.png"))
    }

    @Test
    fun returnsNullForAnEmptyOrUnmatchedCatalog() {
        assertNull(LastPlayedChannelResolver.resolve(emptyList(), null, "News", null))
        assertNull(LastPlayedChannelResolver.resolve(channels, null, "Unknown", null))
    }
}
"""

def replace_once(src, old, new, label):
    if new in src:
        return src
    n = src.count(old)
    if n != 1:
        raise RuntimeError(f"{label}: expected one match, found {n}.")
    return src.replace(old, new, 1)

def remove_once(src, old, label):
    n = src.count(old)
    if n == 0:
        return src
    if n != 1:
        raise RuntimeError(f"{label}: expected one match, found {n}.")
    return src.replace(old, "", 1)

def patch_activity(s):
    s = replace_once(s, "import com.angulismotv.data.FavoritesStore\n",
        "import com.angulismotv.data.FavoritesStore\nimport com.angulismotv.data.LastPlayedChannelStore\n",
        "import LastPlayedChannelStore")
    s = replace_once(s, "    private var currentChannelIndex: Int = 0\n",
        "    private var currentChannelIndex: Int = 0\n"
        "    private val lastPlayedChannelStore by lazy(LazyThreadSafetyMode.NONE) { LastPlayedChannelStore(this) }\n",
        "register last-channel store with playback state")
    s = replace_once(s,
        '            getSharedPreferences("angulismotv_playback", MODE_PRIVATE).edit()\n'
        '                .putString("last_channel_key", ChannelIdentity.key(channel))\n'
        '                .putString("last_channel_name", channel.name)\n'
        '                .putString("last_channel_logo", channel.logo)\n'
        '                .apply()\n',
        "            lastPlayedChannelStore.remember(channel)\n", "centralize last-channel persistence")
    s = remove_once(s, "    private lateinit var insetsController: WindowInsetsControllerCompat\n",
                    "remove unread insetsController field")
    s = replace_once(s, "        insetsController = WindowInsetsControllerCompat(window, window.decorView).apply {\n",
                    "        WindowInsetsControllerCompat(window, window.decorView).apply {\n",
                    "make insets controller local")
    for old, label in (
        ("    private var zappingChannelName: TextView? = null\n", "remove unused zapping text field"),
        ("        zappingChannelName = findViewById(R.id.zapping_channel_name)\n", "remove unused zapping text binding"),
        ("        zappingChannelName?.visibility = View.GONE\n", "remove unused zapping text visibility write"),
        ("    private fun visibleControls(): List<View> = playerControlFocusController.visibleControls()\n", "remove unused visibleControls wrapper"),
        ("    private fun updateCastButtonVisibility() = playerControlStateController.updateCastButtonVisibility()\n", "remove unused cast-visibility wrapper"),
        ("    private fun updateTransportControlsVisibility() = playerControlStateController.updateTransportControlsVisibility()\n", "remove unused transport-visibility wrapper"),
        ("    private fun updateNativeTransportControls() = playerControlStateController.updateNativeTransportControls()\n", "remove unused native-transport wrapper"),
        ("    private fun configureTvControlFocusOrder() = playerControlStateController.configureTvControlFocusOrder()\n", "remove unused focus-order wrapper"),
        ("    private fun configureNativePlayerFocus() =\n        fullscreenPlaybackSurfaceController.configureNativePlayerFocus()\n", "remove unused native-focus wrapper"),
    ):
        s = remove_once(s, old, label)
    s = replace_once(s, "            onChannelSelected = ::selectChannelFromSidePanel,\n",
                    "            onChannelSelected = { channel, _ -> selectChannelFromSidePanel(channel) },\n",
                    "ignore unused panel position")
    s = replace_once(s, "    private fun selectChannelFromSidePanel(channel: Channel, position: Int) {\n",
                    "    private fun selectChannelFromSidePanel(channel: Channel) {\n",
                    "remove unused panel position argument")
    return s

def patch_fragment(s):
    s = replace_once(s, "import com.angulismotv.data.ChannelFilterEngine\n",
        "import com.angulismotv.data.ChannelFilterEngine\nimport com.angulismotv.data.LastPlayedChannelStore\n",
        "import LastPlayedChannelStore in ChannelsFragment")
    s = replace_once(s, "    private var inlineTimelineController: PlayerTimelineController? = null\n",
        "    private var inlineTimelineController: PlayerTimelineController? = null\n"
        "    private val lastPlayedChannelStore by lazy(LazyThreadSafetyMode.NONE) { LastPlayedChannelStore(requireContext()) }\n",
        "register shared store beside inline playback state")
    old_save = '''        requireContext().getSharedPreferences("angulismotv_playback", android.content.Context.MODE_PRIVATE)
            .edit()
            .putString("last_channel_key", ChannelIdentity.key(channel))
            .putString("last_channel_name", channel.name)
            .putString("last_channel_logo", channel.logo)
            .apply()'''
    s = replace_once(s, old_save, "        lastPlayedChannelStore.remember(channel)", "centralize last-channel save")
    old_restore = '''        val preferences = requireContext().getSharedPreferences(
            "angulismotv_playback",
            android.content.Context.MODE_PRIVATE
        )
        val savedKey = preferences.getString("last_channel_key", null)
        val savedName = preferences.getString("last_channel_name", null).orEmpty()
        val savedLogo = preferences.getString("last_channel_logo", null)
        val lastChannel = channels.firstOrNull {
            !savedKey.isNullOrBlank() && ChannelIdentity.key(it) == savedKey
        } ?: channels.firstOrNull {
            savedName.isNotBlank() && it.name.equals(savedName, ignoreCase = true) &&
                (savedLogo.isNullOrBlank() || it.logo == savedLogo)
        } ?: channels.firstOrNull {
            savedName.isNotBlank() && it.name.equals(savedName, ignoreCase = true)
        } ?: return'''
    s = replace_once(s, old_restore, "        val lastChannel = lastPlayedChannelStore.resolve(channels) ?: return",
                     "centralize last-channel resolution")
    old_clear = '''            requireContext().getSharedPreferences("angulismotv_playback", android.content.Context.MODE_PRIVATE)
                .edit().clear().apply()'''
    s = replace_once(s, old_clear, "            lastPlayedChannelStore.clear()", "centralize last-channel clearing")
    return s

def main():
    if len(sys.argv) != 2:
        raise SystemExit("Uso: apply_unified_player_cleanup.py <project-dir>")
    root = Path(sys.argv[1]).resolve()
    if not root.is_dir():
        raise SystemExit(f"No es un directorio de proyecto: {root}")
    for relative in (A, F, L, D):
        if not (root / relative).is_file():
            raise SystemExit(f"No se encontró {relative}.")
    updates = {
        A: patch_activity((root / A).read_text(encoding="utf-8")),
        F: patch_fragment((root / F).read_text(encoding="utf-8")),
        L: (root / L).read_text(encoding="utf-8"),
        D: (root / D).read_text(encoding="utf-8"),
    }
    layout = updates[L]
    if 'android:id="@+id/zapping_channel_name"' in layout:
        layout, n = re.subn(r'<TextView\b(?=[^>]*android:id="@\+id/zapping_channel_name")[^>]*/>', "", layout, count=1)
        if n != 1:
            raise SystemExit("No se pudo quitar la etiqueta de zapping sin uso.")
        updates[L] = layout
    dimens = updates[D]
    for name in ("zapping_label_max_width_mobile", "zapping_label_max_width_tv",
                 "zapping_label_margin_start", "text_size_zapping_channel_name"):
        dimens, n = re.subn(rf'<dimen\s+name="{re.escape(name)}">.*?</dimen>\s*', "", dimens)
        if n > 1:
            raise SystemExit(f"Dimensión duplicada: {name}.")
    updates[D] = dimens
    updates[S] = STORE
    updates[T] = TEST
    for relative, content in updates.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            path.write_text(content, encoding="utf-8", newline="\n")
            print("updated", relative)
    print("UnifiedPlayerActivity cleanup: OK.")

if __name__ == "__main__":
    main()
