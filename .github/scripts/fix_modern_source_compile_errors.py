#!/usr/bin/env python3
"""Apply small, validated compile fixes to the current modular source ZIP tree."""
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve()


def patch_file(relative_path: str, replacements: tuple[tuple[str, str, str], ...]) -> None:
    path = ROOT / relative_path
    if not path.is_file():
        raise SystemExit(f"Modern source compile fix: missing expected file: {relative_path}")
    source = path.read_text(encoding="utf-8")
    changed = False
    for old, new, label in replacements:
        if old in source:
            if source.count(old) != 1:
                raise SystemExit(
                    f"Modern source compile fix ({label}): expected one match, found {source.count(old)}"
                )
            source = source.replace(old, new, 1)
            changed = True
        elif new not in source:
            raise SystemExit(f"Modern source compile fix ({label}): source no longer matches known variants")
    if changed:
        path.write_text(source, encoding="utf-8", newline="\n")
        print(f"fixed {relative_path}")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: fix_modern_source_compile_errors.py <project-root>", file=sys.stderr)
        return 2
    if not (ROOT / "settings.gradle.kts").is_file():
        raise SystemExit(f"Not a Gradle project root: {ROOT}")

    fragment = "app/src/main/java/com/angulismotv/fragments/ChannelsFragment.kt"
    patch_file(fragment, (
        (
            'putParcelableExtra("current_channel", channel)',
            'putExtra("current_channel", channel)',
            "store current channel in Intent",
        ),
        (
            "val key = returnedSession.channel.name to returnedSession.channel.logo",
            "val key = ChannelIdentity.key(returnedSession.channel)",
            "restore focus using canonical channel identity",
        ),
    ))

    engine = "app/src/main/java/com/angulismotv/player/InlinePlaybackEngineController.kt"
    patch_file(engine, (
        (
            "import com.google.android.exoplayer2.Player\n",
            "import com.google.android.exoplayer2.Player\nimport com.google.android.exoplayer2.Tracks\n",
            "import ExoPlayer Tracks listener type",
        ),
    ))

    # Guard the exact listener signature so a future dependency/API change doesn't
    # silently leave diagnostics uncompilable.
    engine_source = (ROOT / engine).read_text(encoding="utf-8")
    if "override fun onTracksChanged(tracks: Tracks)" not in engine_source:
        raise SystemExit("Modern source compile fix: expected ExoPlayer Tracks listener signature is absent")

    print("Modern source compile fixes applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
