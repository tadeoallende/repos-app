#!/usr/bin/env python3
"""Move native fullscreen player creation/reuse out of UnifiedPlayerActivity."""
from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import zipfile


ENTRY = "app/src/main/java/com/angulismotv/UnifiedPlayerActivity.kt"


def replace_once(source: str, old: str, new: str, label: str) -> str:
    if source.count(old) != 1:
        raise RuntimeError(
            f"No se pudo modularizar UnifiedPlayerActivity ({label}): "
            f"se esperaba una coincidencia y se encontraron {source.count(old)}."
        )
    return source.replace(old, new, 1)


def patch_activity(source: str) -> str:
    if "private val fullscreenNativePlaybackController by lazy" in source:
        return source

    source = replace_once(
        source,
        "import com.angulismotv.player.StreamMediaSourceFactory\n",
        "import com.angulismotv.player.FullscreenNativePlaybackController\n",
        "actualizar importaciones"
    )
    source = replace_once(
        source,
        "class UnifiedPlayerActivity : AppCompatActivity() {\n\n"
        "    private val playerControlsAnimator = PlayerControlsAnimator()",
        "class UnifiedPlayerActivity : AppCompatActivity() {\n\n"
        "    private val fullscreenNativePlaybackController by lazy(LazyThreadSafetyMode.NONE) {\n"
        "        FullscreenNativePlaybackController(\n"
        "            context = this,\n"
        "            playerView = playerView,\n"
        "            playerEvents = fullscreenPlayerEvents,\n"
        "            setCurrentPlayer = { exoPlayer = it },\n"
        "            onPlayStateChanged = ::updatePlayPauseButton\n"
        "        )\n"
        "    }\n\n"
        "    private val playerControlsAnimator = PlayerControlsAnimator()",
        "registrar controlador nativo"
    )
    source = replace_once(
        source,
        "        if (reuseInlinePlayerIfAvailable(url, type, generation)) return\n"
        "        try {\n"
        "            createAndStartExoPlayer(url, type, generation, playWhenReady)\n",
        "        if (fullscreenNativePlaybackController.reuseInlinePlayerIfAvailable(\n"
        "                enabled = intent.getBooleanExtra(\"reuse_inline_player_session\", false),\n"
        "                url = url,\n"
        "                type = type,\n"
        "                generation = generation\n"
        "            )) return\n"
        "        try {\n"
        "            fullscreenNativePlaybackController.createAndStart(url, type, generation, playWhenReady)\n",
        "delegar creación y reutilización nativa"
    )

    start_marker = "    /** Reuses an inline session only when the handoff contains the existing native player. */"
    end_marker = "    /** Returns the active playback session and latest channel selection before fullscreen exits. */"
    start = source.find(start_marker)
    end = source.find(end_marker, start + len(start_marker))
    if start < 0 or end < 0:
        raise RuntimeError(
            "No se pudo retirar la implementación nativa duplicada de UnifiedPlayerActivity."
        )
    block = source[start:end]
    if "private fun reuseInlinePlayerIfAvailable" not in block or "private fun createAndStartExoPlayer" not in block:
        raise RuntimeError("El bloque a retirar no contiene ambos métodos esperados.")
    return source[:start] + source[end:]


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: apply_fullscreen_player_modularization.py <proyecto.zip>", file=sys.stderr)
        return 2
    archive = Path(sys.argv[1]).resolve()
    if not archive.is_file() or not zipfile.is_zipfile(archive):
        print(f"No es un ZIP válido: {archive}", file=sys.stderr)
        return 2

    with zipfile.ZipFile(archive, "r") as source:
        names = source.namelist()
        if ENTRY not in names:
            raise SystemExit(f"No se encontró {ENTRY} en el ZIP.")
        content = source.read(ENTRY).decode("utf-8")
        patched = patch_activity(content).encode("utf-8")
        fd, temp_name = tempfile.mkstemp(prefix=archive.stem + "-native-player-", suffix=".zip", dir=archive.parent)
        os.close(fd)
        temp = Path(temp_name)
        try:
            with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED) as target:
                for info in source.infolist():
                    data = patched if info.filename == ENTRY else source.read(info.filename)
                    target.writestr(info, data)
            with zipfile.ZipFile(temp, "r") as result:
                damaged_entry = result.testzip()
                if damaged_entry:
                    raise RuntimeError(f"ZIP dañado después de modularizar el reproductor: {damaged_entry}")
            os.replace(temp, archive)
        finally:
            if temp.exists():
                temp.unlink()

    print("UnifiedPlayerActivity: creación y reutilización de ExoPlayer delegadas a FullscreenNativePlaybackController.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
