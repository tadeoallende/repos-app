#!/usr/bin/env python3
"""Extract native playback surface transitions from UnifiedPlayerActivity."""
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
            f"No se pudo modularizar la superficie del reproductor ({label}): "
            f"se esperaba una coincidencia y se encontraron {count}."
        )
    return source.replace(old, new, 1)


def patch_activity(source: str) -> str:
    if "private val fullscreenPlaybackSurfaceController by lazy" in source:
        return source

    source = replace_once(
        source,
        "import com.angulismotv.player.FullscreenNativePlaybackController\n",
        "import com.angulismotv.player.FullscreenNativePlaybackController\n"
        "import com.angulismotv.player.FullscreenPlaybackSurfaceController\n",
        "importar controlador de superficie"
    )
    source = replace_once(
        source,
        "    private val playerControlsAnimator = PlayerControlsAnimator()",
        "    private val fullscreenPlaybackSurfaceController by lazy(LazyThreadSafetyMode.NONE) {\n"
        "        FullscreenPlaybackSurfaceController(\n"
        "            playerTimelineContainer = playerTimelineContainer,\n"
        "            playerView = playerView,\n"
        "            webView = webView,\n"
        "            webViewTouchBlocker = webViewTouchBlocker,\n"
        "            progressBar = progressBar,\n"
        "            errorText = errorText,\n"
        "            isTV = { isTV },\n"
        "            stopTimelineUpdates = ::stopTimelineUpdates,\n"
        "            invalidatePendingWebLoad = { webViewPlaybackController.invalidatePendingLoad() },\n"
        "            stopRecoveryWatchdog = { recovery.stopWatchdog() },\n"
        "            releasePlayer = ::releasePlayer,\n"
        "            stopWebBridgeMonitor = { webBridge.stopMonitor() },\n"
        "            detachWebBridge = { webBridge.detach() },\n"
        "            setCurrentIsLive = { currentIsLive = it },\n"
        "            setStreamIsLive = { streamIsLive = it },\n"
        "            setCurrentStreamType = { currentStreamType = it },\n"
        "            currentGeneration = { playerGeneration },\n"
        "            lockWebViewFocus = ::lockWebViewFocus\n"
        "        )\n"
        "    }\n\n"
        "    private val playerControlsAnimator = PlayerControlsAnimator()",
        "registrar controlador de superficie"
    )

    old_prepare = """    /** Clears the previous renderer and prepares a clean surface for native playback. */
    private fun prepareNativePlaybackSurface(type: String): Int {
        playerTimelineContainer.visibility = View.GONE
        stopTimelineUpdates()
        webViewPlaybackController.invalidatePendingLoad()
        recovery.stopWatchdog()
        releasePlayer()

        val hadVisibleWebView = webView.visibility == View.VISIBLE
        playerView.visibility = View.VISIBLE
        webView.visibility = View.GONE
        webViewTouchBlocker.visibility = View.GONE
        progressBar.visibility = View.VISIBLE
        errorText.visibility = View.GONE
        currentIsLive = false
        streamIsLive = false
        if (hadVisibleWebView) {
            // Detach an old iframe before switching its view to native video, to avoid background audio.
            webBridge.stopMonitor()
            webBridge.detach()
            webView.stopLoading()
            webView.loadUrl("about:blank")
        }
        currentStreamType = type
        configureNativePlayerFocus()
        return playerGeneration
    }

    private fun configureNativePlayerFocus() {
        if (!isTV) return
        playerView.isFocusable = true
        playerView.isFocusableInTouchMode = true
        playerView.requestFocus()
        lockWebViewFocus()
    }
"""
    new_prepare = """    /** Clears the previous renderer and prepares a clean surface for native playback. */
    private fun prepareNativePlaybackSurface(type: String): Int =
        fullscreenPlaybackSurfaceController.prepareNativePlaybackSurface(type)

    private fun configureNativePlayerFocus() =
        fullscreenPlaybackSurfaceController.configureNativePlayerFocus()
"""
    return replace_once(source, old_prepare, new_prepare, "extraer transición de superficie")


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: apply_fullscreen_surface_modularization.py <proyecto.zip>", file=sys.stderr)
        return 2
    archive = Path(sys.argv[1]).resolve()
    if not archive.is_file() or not zipfile.is_zipfile(archive):
        print(f"No es un ZIP válido: {archive}", file=sys.stderr)
        return 2
    with zipfile.ZipFile(archive, "r") as source:
        names = source.namelist()
        if ENTRY not in names:
            raise SystemExit(f"No se encontró {ENTRY} en el ZIP.")
        patched = patch_activity(source.read(ENTRY).decode("utf-8")).encode("utf-8")
        fd, temp_name = tempfile.mkstemp(prefix=archive.stem + "-surface-", suffix=".zip", dir=archive.parent)
        os.close(fd)
        temp = Path(temp_name)
        try:
            with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED) as target:
                for info in source.infolist():
                    target.writestr(info, patched if info.filename == ENTRY else source.read(info.filename))
            with zipfile.ZipFile(temp, "r") as result:
                damaged = result.testzip()
                if damaged:
                    raise RuntimeError(f"ZIP dañado después de modularizar la superficie: {damaged}")
            os.replace(temp, archive)
        finally:
            if temp.exists():
                temp.unlink()
    print("UnifiedPlayerActivity: transición de superficie nativa delegada a FullscreenPlaybackSurfaceController.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
