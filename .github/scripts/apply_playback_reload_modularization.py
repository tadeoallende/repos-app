#!/usr/bin/env python3
"""Delegate manual playback reload orchestration from UnifiedPlayerActivity."""
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
            f"No se pudo modularizar la recarga del reproductor ({label}): "
            f"se esperaba una coincidencia y se encontraron {count}."
        )
    return source.replace(old, new, 1)


def patch_activity(source: str) -> str:
    if "playbackReloadController.reloadCurrentTransmission()" in source:
        return source

    source = replace_once(
        source,
        "import com.angulismotv.player.PlaybackRecoveryController\n",
        "import com.angulismotv.player.PlaybackRecoveryController\n"
        "import com.angulismotv.player.PlaybackReloadController\n",
        "importar controlador"
    )

    source = replace_once(
        source,
        "    private val playerControlsAnimator = PlayerControlsAnimator()",
        "    private val playbackReloadController by lazy(LazyThreadSafetyMode.NONE) {\n"
        "        PlaybackReloadController(\n"
        "            selectedChannel = { currentChannel },\n"
        "            currentUrl = { currentStreamUrl },\n"
        "            currentType = { currentStreamType },\n"
        "            isHttpUrl = { url -> StreamUrlPolicy.isHttpUrl(url) },\n"
        "            isIframeType = { type -> type == StreamType.IFRAME },\n"
        "            prepareForReload = {\n"
        "                playerGeneration++\n"
        "                isZapping = false\n"
        "                cancelOptionFallback()\n"
        "                fullscreenPlayerEvents.clearStableStreamTimer()\n"
        "                recovery.reset(cancelPendingReconnect = true)\n"
        "                webViewPlaybackController.invalidatePendingLoad()\n"
        "                errorText.visibility = View.GONE\n"
        "                progressBar.visibility = View.VISIBLE\n"
        "            },\n"
        "            reloadIframe = { url ->\n"
        "                // A manual iframe reload must start a fresh navigation, not reuse a stale page.\n"
        "                reuseInlineWebViewOnLoad = false\n"
        "                webViewPlaybackController.load(url, reuseLoadedPage = false)\n"
        "            },\n"
        "            reloadStream = ::playStream,\n"
        "            fallbackToFirstOption = ::playFirstValidOption,\n"
        "            controlsVisible = { controlsVisible },\n"
        "            resetAutoHideTimer = ::resetAutoHideTimer,\n"
        "            showMissingChannelError = { showError(\"No hay ningún canal seleccionado para recargar.\") }\n"
        "        )\n"
        "    }\n\n"
        "    private val playerControlsAnimator = PlayerControlsAnimator()",
        "registrar controlador"
    )

    old_method = """    /** Reintenta la fuente actual sin cambiar de canal ni reiniciar la selección del usuario. */
    private fun reloadCurrentTransmission() {
        val channel = currentChannel
        if (channel == null) {
            showError("No hay ningún canal seleccionado para recargar.")
            return
        }

        playerGeneration++
        isZapping = false
        cancelOptionFallback()
        fullscreenPlayerEvents.clearStableStreamTimer()
        recovery.reset(cancelPendingReconnect = true)
        webViewPlaybackController.invalidatePendingLoad()
        errorText.visibility = View.GONE
        progressBar.visibility = View.VISIBLE

        val url = currentStreamUrl
        val type = currentStreamType
        if (url.isNotBlank() && StreamUrlPolicy.isHttpUrl(url)) {
            currentStreamUrl = url
            currentStreamType = type
            if (type == StreamType.IFRAME) {
                // Forzar navegación nueva; no reutilizar el documento del iframe que pudo fallar.
                reuseInlineWebViewOnLoad = false
                webViewPlaybackController.load(url, reuseLoadedPage = false)
            } else {
                playStream(url, type)
            }
        } else {
            playFirstValidOption(channel)
        }

        if (controlsVisible) resetAutoHideTimer()
    }"""
    new_method = """    /** Reintenta la fuente actual sin cambiar de canal ni reiniciar la selección del usuario. */
    private fun reloadCurrentTransmission() =
        playbackReloadController.reloadCurrentTransmission()"""
    return replace_once(source, old_method, new_method, "delegar recarga manual")


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: apply_playback_reload_modularization.py <proyecto.zip>", file=sys.stderr)
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
        fd, temp_name = tempfile.mkstemp(prefix=archive.stem + "-reload-", suffix=".zip", dir=archive.parent)
        os.close(fd)
        temp = Path(temp_name)
        try:
            with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED) as target:
                for info in source.infolist():
                    target.writestr(info, patched if info.filename == ENTRY else source.read(info.filename))
            with zipfile.ZipFile(temp, "r") as result:
                damaged = result.testzip()
                if damaged:
                    raise RuntimeError(f"ZIP dañado después de modularizar la recarga: {damaged}")
            os.replace(temp, archive)
        finally:
            if temp.exists():
                temp.unlink()
    print("UnifiedPlayerActivity: recarga manual delegada a PlaybackReloadController.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
