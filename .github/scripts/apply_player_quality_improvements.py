#!/usr/bin/env python3
"""Apply targeted, idempotent quality fixes to the generated fullscreen player Activity."""
from __future__ import annotations
import os
from pathlib import Path
import re
import sys
import tempfile
import zipfile

ENTRY = "app/src/main/java/com/angulismotv/UnifiedPlayerActivity.kt"

def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"No se pudo mejorar UnifiedPlayerActivity ({label}): se esperaba una coincidencia y se encontraron {count}.")
    return source.replace(old, new, 1)

def replace_region(source: str, start_marker: str, end_marker: str, replacement: str, label: str) -> str:
    if source.count(start_marker) != 1:
        raise RuntimeError(f"No se encontró una única apertura para {label}.")
    start = source.index(start_marker)
    end = source.find(end_marker, start + len(start_marker))
    if end < 0:
        raise RuntimeError(f"No se encontró el cierre de región para {label}.")
    return source[:start] + replacement.rstrip() + "\n\n" + source[end:]

def promote_lazy_delegate(source: str, property_name: str) -> str:
    """Expose a Lazy<T> delegate so onDestroy can dispose it without forcing initialization."""
    old_header = f"    private val {property_name} by lazy(LazyThreadSafetyMode.NONE) {{"
    delegate_header = f"    private val {property_name}Delegate = lazy(LazyThreadSafetyMode.NONE) {{"
    if delegate_header in source and f"private val {property_name} by {property_name}Delegate" in source:
        return source
    if source.count(old_header) != 1:
        raise RuntimeError(f"No se encontró una única declaración lazy para {property_name}.")
    source = source.replace(old_header, delegate_header, 1)
    header_index = source.index(delegate_header)
    close_index = source.find("\n    }\n", header_index + len(delegate_header))
    if close_index < 0:
        raise RuntimeError(f"No se pudo encontrar el cierre lazy de {property_name}.")
    close_end = close_index + len("\n    }")
    source = source[:close_end] + f"\n    private val {property_name} by {property_name}Delegate" + source[close_end:]
    return source

def patch_activity(source: str) -> str:
    if "pendingZapAccumulator" in source and "private fun revealControls(temporarily: Boolean)" in source:
        return source
    source = replace_once(
        source, "package com.angulismotv\n",
        "package com.angulismotv\n\n"
        "import androidx.activity.OnBackPressedCallback\n"
        "import androidx.core.content.IntentCompat\n"
        "import com.angulismotv.player.ChannelZapAccumulator\n",
        "agregar dependencias AndroidX"
    )
    source = replace_once(
        source, "    private var isZapping = false\n",
        "    private var isZapping = false\n    private val pendingZapAccumulator = ChannelZapAccumulator()\n",
        "registrar acumulador de zapping"
    )
    source = replace_region(
        source, "    private fun changeChannel(delta: Int) {",
        "    private fun zapTo(index: Int, channel: Channel) {",
        """    private fun changeChannel(delta: Int) {
        if (allChannels.isEmpty()) {
            pendingZapAccumulator.clear()
            return
        }
        if (isZapping) {
            pendingZapAccumulator.accumulate(delta)
            return
        }
        val targetIndex = (currentChannelIndex + delta).mod(allChannels.size)
        zapTo(targetIndex, allChannels[targetIndex])
    }

    /** Applies accumulated CH+/CH- presses after the active channel transition is complete. */
    private fun dispatchPendingZap() {
        if (isZapping) return
        val delta = pendingZapAccumulator.consume()
        if (delta == 0 || allChannels.isEmpty()) return
        changeChannel(delta)
    }""",
        "acumular el zapping y calcular el índice una vez"
    )
    source = replace_once(
        source,
        "    private fun zapTo(index: Int, channel: Channel) {\n        cancelPendingZappingReset()\n        isZapping = true\n",
        "    private fun zapTo(index: Int, channel: Channel) {\n        cancelPendingZappingReset()\n        pendingZapAccumulator.clear()\n        isZapping = true\n",
        "limpiar cola al iniciar un zapping directo"
    )
    source = replace_once(
        source,
        "                isZapping = false\n                clearZappingRunnable = null\n",
        "                isZapping = false\n                clearZappingRunnable = null\n                dispatchPendingZap()\n",
        "procesar cola al terminar el zapping"
    )
    source = replace_once(source, "        mainHandler.postDelayed(zapRunnable!!, ZAPPING_START_DELAY_MS)\n",
                          "        zapRunnable?.let { mainHandler.postDelayed(it, ZAPPING_START_DELAY_MS) }\n",
                          "evitar !! en zapRunnable")
    source = replace_once(source, "        mainHandler.postDelayed(hideControlsRunnable!!, 5_000)\n",
                          "        hideControlsRunnable?.let { mainHandler.postDelayed(it, 5_000) }\n",
                          "evitar !! en hideControlsRunnable")
    source = replace_once(
        source,
        "                playerGeneration++\n                isZapping = false\n                cancelOptionFallback()\n",
        "                playerGeneration++\n                cancelPendingZappingReset()\n                pendingZapAccumulator.clear()\n                isZapping = false\n                cancelOptionFallback()\n",
        "cancelar cola si recargan la transmisión"
    )
    source = replace_once(source, "        mainHandler.removeCallbacksAndMessages(null)\n",
                          "        pendingZapAccumulator.clear()\n        zapRunnable = null\n        mainHandler.removeCallbacksAndMessages(null)\n",
                          "limpiar cola al destruir Activity")
    source = replace_once(
        source,
        "        val selectedInFiltered = channelPanelController.filteredChannels.indexOfFirst { currentChannel != null && ChannelIdentity.same(it, currentChannel!!) }\n",
        "        val selectedCurrentChannel = currentChannel\n"
        "        val selectedInFiltered = channelPanelController.filteredChannels.indexOfFirst {\n"
        "            selectedCurrentChannel != null && ChannelIdentity.same(it, selectedCurrentChannel)\n"
        "        }\n",
        "eliminar !! en selección filtrada"
    )
    channel_block_pattern = re.compile(
        r"(?m)^(?P<indent>[ \t]*)currentChannel = allChannels\[currentChannelIndex\]\n"
        r"(?P=indent)loadChannelInfo\(currentChannel!!\)\n"
        r"(?P=indent)updateFavoriteButton\(currentChannel!!\)\n"
    )
    def replace_channel_block(match: re.Match[str]) -> str:
        indent = match.group("indent")
        child = indent + "    "
        return (
            f"{indent}val selectedChannel = allChannels.getOrNull(currentChannelIndex) ?: return\n"
            f"{indent}currentChannel = selectedChannel\n"
            f"{indent}loadChannelInfo(selectedChannel)\n"
            f"{indent}updateFavoriteButton(selectedChannel)\n"
            f"{indent}val selectedOptions = selectedChannel.options.orEmpty()\n"
        )
    source, channel_block_count = channel_block_pattern.subn(replace_channel_block, source, count=1)
    if channel_block_count != 1:
        raise RuntimeError("No se encontró el bloque de canal actual al eliminar aserciones !!.")

    option_block_pattern = re.compile(
        r"(?m)^(?P<indent>[ \t]*)if \(!currentChannel!!\.options\.isNullOrEmpty\(\) && requestedSourceIndex in currentChannel!!\.options!!\.indices\) \{\n"
        r"(?P=indent)    tryOption\(currentChannel!!, requestedSourceIndex\)\n"
        r"(?P=indent)\} else \{\n"
        r"(?P=indent)    playFirstValidOption\(currentChannel!!\)\n"
        r"(?P=indent)\}\n"
    )
    def replace_option_block(match: re.Match[str]) -> str:
        indent = match.group("indent")
        child = indent + "    "
        return (
            f"{indent}if (selectedOptions.isNotEmpty() && requestedSourceIndex in selectedOptions.indices) {{\n"
            f"{child}tryOption(selectedChannel, requestedSourceIndex)\n"
            f"{indent}}} else {{\n"
            f"{child}playFirstValidOption(selectedChannel)\n"
            f"{indent}}}\n"
        )
    source, option_block_count = option_block_pattern.subn(replace_option_block, source, count=1)
    if option_block_count != 1:
        raise RuntimeError("No se encontró el bloque de opciones al eliminar aserciones !!.")
    source = replace_once(source, "        loadChannelInfo(currentChannel!!)\n",
                          "        currentChannel?.let(::loadChannelInfo)\n",
                          "eliminar !! durante el zapping")
    source = replace_once(source, "            hasLegacyCatalog -> legacyCatalog!!\n",
                          "            hasLegacyCatalog -> legacyCatalog.orEmpty()\n",
                          "eliminar !! del catálogo heredado")
    source = replace_once(source, '        val singleChannel = intent.getParcelableExtra<Channel>("current_channel")\n',
                          '        val singleChannel = IntentCompat.getParcelableExtra(intent, "current_channel", Channel::class.java)\n',
                          "migrar Parcelable a IntentCompat")
    source = re.sub(
        r'(?m)^([ \t]*)@Suppress\("DEPRECATION"\)\n(?=[ \t]*val singleChannel = IntentCompat\.getParcelableExtra)', "", source
    )
    source = replace_once(
        source,
        "    override fun onCreate(savedInstanceState: Bundle?) {\n"
        "        super.onCreate(savedInstanceState)\n"
        "        if (!DeviceHelper.isTV(this)) enableImmersiveFullscreen()\n"
        "        setContentView(R.layout.activity_unified_player)\n\n"
        "        isTV = DeviceHelper.isTV(this)\n"
        "        bindViews()\n",
        "    override fun onCreate(savedInstanceState: Bundle?) {\n"
        "        super.onCreate(savedInstanceState)\n"
        "        isTV = DeviceHelper.isTV(this)\n"
        "        if (!isTV) enableImmersiveFullscreen()\n"
        "        setContentView(R.layout.activity_unified_player)\n"
        "        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {\n"
        "            override fun handleOnBackPressed() {\n"
        "                if (!isTV) finish()\n"
        "            }\n"
        "        })\n\n"
        "        bindViews()\n",
        "centralizar detección de dispositivo y back dispatcher"
    )
    source = replace_region(source, "    override fun onBackPressed() {",
                            "    // ==================== BIND VIEWS ====================", "",
                            "retirar onBackPressed obsoleto")
    source = replace_region(
        source, "    private fun updateWebViewControls() {",
        "    // ==================== SIDE PANEL ====================",
        """    private fun updateWebViewControls() {
        runOnUiThread {
            if (currentStreamType != StreamType.IFRAME) return@runOnUiThread
            // Reutiliza la política común de transporte para TV y móvil.
            updateIframeTransportControls()
            btnOptions.visibility = if (hasMultipleOptions()) View.VISIBLE else View.GONE
            if (isTV) {
                btnMenu.visibility = View.VISIBLE
                btnMenu.isFocusable = true
                btnClose.isFocusable = true
            }
            if (controlsVisible) {
                bottomControls.visibility = View.VISIBLE
                bottomControls.bringToFront()
            }
            updateControlFocusOrder()
        }
    }""",
        "unificar estado de controles iframe"
    )
    source = replace_region(
        source, "    private fun showControls() {", "    private fun hideControls() {",
        """    private fun showControls() = revealControls(temporarily = false)

    private fun showControlsTemporarily() = revealControls(temporarily = true)

    private fun revealControls(temporarily: Boolean) {
        updateControlsVisibility()
        // Los controles son independientes del motor; también aparecen sobre WebView/iframe.
        playerControlsAnimator.show(controlsOverlay, slide = false)
        playerControlsAnimator.show(bottomControls, slide = true)
        if (!isTV) playerControlsAnimator.show(findViewById(R.id.center_transport_controls_container), slide = false)
        bottomControls.bringToFront()
        controlsVisible = true
        updatePlayerTimeline()
        if (isTV && !temporarily) requestPreferredControlFocus()
        if (!isTV && temporarily) startTimelineUpdates()
        resetAutoHideTimer()
    }""",
        "unificar la presentación de controles"
    )
    for name in ("orientationController", "recovery", "sourceSelectionController"):
        source = promote_lazy_delegate(source, name)
    source = replace_once(source, "        orientationController.dispose()\n",
                          "        if (orientationControllerDelegate.isInitialized()) orientationController.dispose()\n",
                          "no inicializar orientación solo para destruir")
    source = replace_once(source, "        sourceSelectionController.dispose()\n",
                          "        if (sourceSelectionControllerDelegate.isInitialized()) sourceSelectionController.dispose()\n",
                          "no inicializar selección solo para destruir")
    source = replace_once(source, "        recovery.dispose()\n",
                          "        if (recoveryDelegate.isInitialized()) recovery.dispose()\n",
                          "no inicializar recovery solo para destruir")
    remaining = [(n, line) for n, line in enumerate(source.splitlines(), 1) if "!!" in line]
    if remaining:
        details = "\n".join(f"{n}: {line}" for n, line in remaining)
        raise RuntimeError("Quedaron aserciones no nulas en UnifiedPlayerActivity:\n" + details)
    if source.count("DeviceHelper.isTV(this)") != 1:
        raise RuntimeError("UnifiedPlayerActivity todavía calcula isTV más de una vez.")
    return source

def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: apply_player_quality_improvements.py <proyecto.zip>", file=sys.stderr)
        return 2
    archive = Path(sys.argv[1]).resolve()
    if not archive.is_file() or not zipfile.is_zipfile(archive):
        raise SystemExit(f"No es un ZIP válido: {archive}")
    fd, temporary_name = tempfile.mkstemp(prefix=archive.stem + "-player-quality-", suffix=".zip", dir=archive.parent)
    os.close(fd)
    temporary = Path(temporary_name)
    changed = False
    try:
        with zipfile.ZipFile(archive, "r") as source, zipfile.ZipFile(
            temporary, "w", compression=zipfile.ZIP_DEFLATED
        ) as target:
            entries = source.infolist()
            if sum(1 for info in entries if info.filename == ENTRY) != 1:
                raise RuntimeError(f"Se esperaba una única entrada {ENTRY} en el ZIP.")
            for info in entries:
                data = source.read(info)
                if info.filename == ENTRY:
                    original = data.decode("utf-8")
                    updated = patch_activity(original)
                    changed = updated != original
                    data = updated.encode("utf-8")
                target.writestr(info, data)
        with zipfile.ZipFile(temporary, "r") as result:
            damaged = result.testzip()
            if damaged:
                raise RuntimeError(f"ZIP dañado tras mejorar el reproductor: {damaged}")
        os.replace(temporary, archive)
    finally:
        if temporary.exists():
            temporary.unlink()
    print("UnifiedPlayerActivity: zapping acumulativo, controles unificados, IntentCompat, back callback, cleanup lazy y sin !! " + ("aplicados." if changed else "ya estaban aplicados."))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
