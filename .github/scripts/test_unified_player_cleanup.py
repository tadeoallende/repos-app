#!/usr/bin/env python3
"""Static regression checks for UnifiedPlayerActivity cleanup."""
from pathlib import Path
import sys

FILES = {
    "activity": "app/src/main/java/com/angulismotv/UnifiedPlayerActivity.kt",
    "fragment": "app/src/main/java/com/angulismotv/fragments/ChannelsFragment.kt",
    "layout": "app/src/main/res/layout/activity_unified_player.xml",
    "dimens": "app/src/main/res/values/dimens.xml",
    "store": "app/src/main/java/com/angulismotv/data/LastPlayedChannelStore.kt",
    "tests": "app/src/test/java/com/angulismotv/data/LastPlayedChannelResolverTest.kt",
}

def main():
    if len(sys.argv) != 2:
        raise SystemExit("Uso: test_unified_player_cleanup.py <project-dir>")
    root = Path(sys.argv[1]).resolve()
    source = {name: (root / path).read_text(encoding="utf-8") for name, path in FILES.items()}
    dead = (
        "private fun visibleControls()",
        "private fun updateCastButtonVisibility()",
        "private fun updateTransportControlsVisibility()",
        "private fun updateNativeTransportControls()",
        "private fun configureTvControlFocusOrder()",
        "private fun configureNativePlayerFocus()",
        "private lateinit var insetsController:",
        "private var zappingChannelName:",
        "zappingChannelName = findViewById",
        "zappingChannelName?.visibility",
    )
    remaining = [item for item in dead if item in source["activity"]]
    if remaining:
        raise SystemExit("Persisten miembros sin uso: " + ", ".join(remaining))
    if source["activity"].count("WindowInsetsControllerCompat(window, window.decorView).apply") != 1:
        raise SystemExit("La configuración de insets no quedó como única instancia local.")
    if 'android:id="@+id/zapping_channel_name"' in source["layout"]:
        raise SystemExit("Sigue el TextView de zapping que nunca se mostraba.")
    for name in ("zapping_label_max_width_mobile", "zapping_label_max_width_tv",
                 "zapping_label_margin_start", "text_size_zapping_channel_name"):
        if f'name="{name}"' in source["dimens"]:
            raise SystemExit("Persisten dimensiones sin uso: " + name)
    if "lastPlayedChannelStore.remember(channel)" not in source["activity"]:
        raise SystemExit("La Activity no delega la persistencia.")
    if 'getSharedPreferences("angulismotv_playback"' in source["activity"]:
        raise SystemExit("La Activity todavía accede a esas preferencias directamente.")
    for item in ("lastPlayedChannelStore.remember(channel)", "lastPlayedChannelStore.resolve(channels)",
                 "lastPlayedChannelStore.clear()"):
        if item not in source["fragment"]:
            raise SystemExit("El Fragment no delega en el almacén: " + item)
    if 'getSharedPreferences("angulismotv_playback"' in source["fragment"]:
        raise SystemExit("El Fragment todavía duplica las preferencias.")
    for item in ("fun remember(channel: Channel)", "fun resolve(channels: List<Channel>)",
                 "fun clear()", "internal object LastPlayedChannelResolver"):
        if item not in source["store"]:
            raise SystemExit("API faltante en LastPlayedChannelStore: " + item)
    for item in ("prefersStableIdentityWhenItMatches", "fallsBackToCaseInsensitiveNameAndMatchingLogo",
                 "returnsNullForAnEmptyOrUnmatchedCatalog"):
        if item not in source["tests"]:
            raise SystemExit("Caso unitario faltante: " + item)
    print("UnifiedPlayerActivity cleanup regression checks: OK.")

if __name__ == "__main__":
    main()
