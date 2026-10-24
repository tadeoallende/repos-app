#!/usr/bin/env python3
"""Move playback-specific Activity lifecycle orchestration into its own controller."""
from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import zipfile

ENTRY = "app/src/main/java/com/angulismotv/UnifiedPlayerActivity.kt"


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(
            f"No se pudo modularizar el ciclo de vida del reproductor ({label}): "
            f"se esperaba una coincidencia y se encontraron {count}."
        )
    return source.replace(old, new, 1)


def patch_activity(source: str) -> str:
    if "playbackLifecycleController.onPauseBeforeSuper()" in source:
        return source

    source = replace_once(
        source,
        "import com.angulismotv.player.PlaybackReloadController\n",
        "import com.angulismotv.player.PlaybackReloadController\n"
        "import com.angulismotv.player.PlaybackLifecycleController\n",
        "importar controlador de ciclo de vida"
    )

    property_anchor = "    private var resumePlaybackAfterPause = false\n"
    controller_property = """    private var resumePlaybackAfterPause = false

    private val playbackLifecycleController by lazy(LazyThreadSafetyMode.NONE) {
        PlaybackLifecycleController(
            isTV = { isTV },
            isZapping = { isZapping },
            isFinishing = { isFinishing },
            isFromInlinePlayer = { intent.getBooleanExtra("from_inline_player", false) },
            resumeAfterPause = { resumePlaybackAfterPause },
            setResumeAfterPause = { resumePlaybackAfterPause = it },
            nativePlayerWantsPlay = { exoPlayer?.playWhenReady == true },
            playNativePlayer = { exoPlayer?.play() },
            pauseNativePlayer = { exoPlayer?.pause() },
            returnSessionToInline = ::returnSessionToInline,
            orientationOnResume = { orientationController.onResume() },
            orientationOnPause = { orientationController.onPause() },
            enableImmersiveFullscreen = ::enableImmersiveFullscreen,
            startCastDiscovery = { cast.startDiscovery() },
            stopCastDiscovery = { cast.stopDiscovery() },
            resumeWebView = { webView.onResume() },
            pauseWebView = { webView.onPause() },
            stopRecoveryWatchdog = { recovery.stopWatchdog() }
        )
    }
"""
    source = replace_once(
        source, property_anchor, controller_property,
        "registrar controlador de ciclo de vida"
    )

    old_resume = """    override fun onResume() {
        super.onResume()
        orientationController.onResume()
        if (!isTV) enableImmersiveFullscreen()
        cast.startDiscovery()
        webView.onResume()
        if (resumePlaybackAfterPause && !isZapping) exoPlayer?.play()
        resumePlaybackAfterPause = false
    }"""
    new_resume = """    override fun onResume() {
        super.onResume()
        playbackLifecycleController.onResume()
    }"""
    source = replace_once(source, old_resume, new_resume, "delegar onResume")

    old_pause = """    override fun onPause() {
        // Pausar el sensor mientras la Activity no está visible; al volver se comprobará de nuevo
        // la orientación física actual sin perder el hecho de que ya se había girado a landscape.
        orientationController.onPause()
        // Recordar la intención de reproducción antes de pausar o transferir la sesión.
        resumePlaybackAfterPause = !isZapping && exoPlayer?.playWhenReady == true
        super.onPause()
        if (isFinishing && intent.getBooleanExtra("from_inline_player", false)) {
            returnSessionToInline()
        } else if (!isZapping) {
            exoPlayer?.pause()
        }
        cast.stopDiscovery()
        webView.onPause()
    }"""
    new_pause = """    override fun onPause() {
        playbackLifecycleController.onPauseBeforeSuper()
        super.onPause()
        playbackLifecycleController.onPauseAfterSuper()
    }"""
    source = replace_once(source, old_pause, new_pause, "delegar onPause")

    old_stop = """    override fun onStop() {
        // Do not keep a 5-second watchdog alive while the Activity is not visible.
        recovery.stopWatchdog()
        super.onStop()
        exoPlayer?.pause()
    }"""
    new_stop = """    override fun onStop() {
        playbackLifecycleController.onStopBeforeSuper()
        super.onStop()
        playbackLifecycleController.onStopAfterSuper()
    }"""
    return replace_once(source, old_stop, new_stop, "delegar onStop")


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: apply_playback_lifecycle_modularization.py <proyecto.zip>", file=sys.stderr)
        return 2
    archive = Path(sys.argv[1]).resolve()
    if not archive.is_file() or not zipfile.is_zipfile(archive):
        print(f"No es un ZIP válido: {archive}", file=sys.stderr)
        return 2

    with zipfile.ZipFile(archive, "r") as source:
        if ENTRY not in source.namelist():
            raise SystemExit(f"No se encontró {ENTRY} en el ZIP.")
        patched = patch_activity(source.read(ENTRY).decode("utf-8")).encode("utf-8")
        fd, temp_name = tempfile.mkstemp(prefix=archive.stem + "-lifecycle-", suffix=".zip", dir=archive.parent)
        os.close(fd)
        temp = Path(temp_name)
        try:
            with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED) as target:
                for info in source.infolist():
                    target.writestr(info, patched if info.filename == ENTRY else source.read(info.filename))
            with zipfile.ZipFile(temp, "r") as result:
                damaged = result.testzip()
                if damaged:
                    raise RuntimeError(f"ZIP dañado después de modularizar el ciclo de vida: {damaged}")
            os.replace(temp, archive)
        finally:
            if temp.exists():
                temp.unlink()

    print("UnifiedPlayerActivity: onResume/onPause/onStop delegados a PlaybackLifecycleController.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
