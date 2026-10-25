#!/usr/bin/env python3
"""Regression guards for the extracted Android TV rail and single-session player handoff."""
from pathlib import Path
import re
import sys

root = Path(sys.argv[1]).resolve()
layout_dir = root / "app/src/main/res/layout"
main_layout = (layout_dir / "activity_main.xml").read_text(encoding="utf-8")
side_layout_path = layout_dir / "view_tv_side_menu.xml"
if not side_layout_path.exists():
    raise SystemExit("FAIL: missing dedicated view_tv_side_menu.xml")
side_layout = side_layout_path.read_text(encoding="utf-8")
if not re.search(r'<include\b[^>]*layout="@layout/view_tv_side_menu"', main_layout):
    raise SystemExit("FAIL: activity_main.xml must include the dedicated TV rail")
for view_id in ("side_menu", "menu_channels", "menu_agenda", "menu_channels_text", "menu_agenda_text"):
    if f'android:id="@+id/{view_id}"' not in side_layout:
        raise SystemExit(f"FAIL: {view_id} must be defined in view_tv_side_menu.xml")
    if f'android:id="@+id/{view_id}"' in main_layout:
        raise SystemExit(f"FAIL: {view_id} must not be duplicated inline in activity_main.xml")

activity = (root / "app/src/main/java/com/angulismotv/MainActivity.kt").read_text(encoding="utf-8")
for member in ("sideMenu", "menuChannels", "menuAgenda", "menuChannelsText", "menuAgendaText"):
    if f"private val {member}:" not in activity:
        raise SystemExit(f"FAIL: MainActivity must resolve {member} from the dedicated layout")
if "binding.menuChannels" in activity or "binding.menuAgenda" in activity or "binding.sideMenu" in activity:
    raise SystemExit("FAIL: MainActivity still depends on child views of activity_main.xml")
if "icon?.setColorFilter" not in activity or "if (selected) R.color.accent else R.color.text_secondary" not in activity:
    raise SystemExit("FAIL: selection must remain expressed by the icon color")

selector = (root / "app/src/main/res/drawable/bg_tv_rail_item.xml").read_text(encoding="utf-8")
selected = re.search(r'<item\s+android:state_selected="true">(.*?)</item>', selector, re.S)
focused = re.search(r'<item\s+android:state_focused="true">(.*?)</item>', selector, re.S)
if not selected or '#00000000' not in selected.group(1):
    raise SystemExit("FAIL: selected rail item background must remain transparent")
if not focused or '#182538' not in focused.group(1):
    raise SystemExit("FAIL: TV D-pad focus affordance must remain visible")

fragment = (root / "app/src/main/java/com/angulismotv/fragments/ChannelsFragment.kt").read_text(encoding="utf-8")
handoff_path = root / "app/src/main/java/com/angulismotv/player/InlinePlayerHandoff.kt"
if not handoff_path.exists():
    raise SystemExit("FAIL: missing InlinePlayerHandoff session owner")
handoff = handoff_path.read_text(encoding="utf-8")

if "private fun prepareInlineHandoff(" in fragment or "private data class InlineHandoffPlan" in fragment:
    raise SystemExit("FAIL: obsolete duplicate handoff implementation remains in ChannelsFragment")

transfer_path = root / "app/src/main/java/com/angulismotv/player/InlinePlayerTransferController.kt"
fullscreen_path = root / "app/src/main/java/com/angulismotv/player/FullscreenNativePlaybackController.kt"
if transfer_path.exists() and fullscreen_path.exists():
    # Later refactored architecture: a dedicated controller mediates the transfer.
    transfer = transfer_path.read_text(encoding="utf-8")
    fullscreen = fullscreen_path.read_text(encoding="utf-8")
    if "inlinePlayerTransferController?.prepare(channel, fromInline)" not in fragment:
        raise SystemExit("FAIL: inline launch must use InlinePlayerTransferController")
    if "offerNativePlayerToFullscreen(channel, player, streamUrl, streamType)" not in transfer:
        raise SystemExit("FAIL: transfer controller must offer the existing native player")
    if "playerView.player = player" not in fullscreen or "// Do not replace media or call prepare()" not in fullscreen:
        raise SystemExit("FAIL: fullscreen reuse must attach existing player without preparing a duplicate")
    if "val player: ExoPlayer?" not in handoff or "player = player" not in transfer:
        raise SystemExit("FAIL: handoff must preserve the existing player instance")
else:
    # Current architecture: the Fragment detaches the active engine into an atomic Session;
    # the fullscreen Activity claims that exact instance only for the matching stream.
    fullscreen_path = root / "app/src/main/java/com/angulismotv/UnifiedPlayerActivity.kt"
    fullscreen = fullscreen_path.read_text(encoding="utf-8")
    required_fragment = (
        "inlinePlaybackEngine.detachForHandoff()",
        "InlinePlayerHandoff.offerToFullscreen(session)",
        'putExtra("reuse_inline_player_session", canTransferNativePlayer)',
    )
    if any(fragment_piece not in fragment for fragment_piece in required_fragment):
        raise SystemExit("FAIL: current inline player does not safely offer its live native session")
    required_fullscreen = (
        'InlinePlayerHandoff.takeForFullscreen(url, type)',
        "playerView.player = player",
        "Do not set a MediaSource or call prepare()",
        "exoPlayer = null // hand the engine back; releasePlayer() must not release it.",
        "InlinePlayerHandoff.returnToInline(",
    )
    if any(piece not in fullscreen for piece in required_fullscreen):
        raise SystemExit("FAIL: current fullscreen player must reuse/return the same native session")
    if "val player: ExoPlayer?" not in handoff or "fun takeForFullscreen(streamUrl: String, streamType: String)" not in handoff:
        raise SystemExit("FAIL: InlinePlayerHandoff must own and validate the transferred player instance")

print("PASS: TV side menu is modular XML with icon-only selection and focus feedback")
print("PASS: mini/fullscreen path uses one existing native player; duplicate legacy path removed")
