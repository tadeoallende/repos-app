#!/usr/bin/env python3
"""Source-level regression checks for UnifiedPlayerActivity quality fixes."""
from __future__ import annotations
from pathlib import Path
import sys

TARGET = Path("app/src/main/java/com/angulismotv/UnifiedPlayerActivity.kt")

def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: test_player_quality.py <project-dir>", file=sys.stderr)
        return 2
    source = (Path(sys.argv[1]).resolve() / TARGET).read_text(encoding="utf-8")
    required = (
        "pendingZapAccumulator.accumulate(delta)",
        "pendingZapAccumulator.consume()",
        "dispatchPendingZap()",
        "private fun revealControls(temporarily: Boolean)",
        "updateIframeTransportControls()",
        "window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)",
        'IntentCompat.getParcelableExtra(intent, "current_channel", Channel::class.java)',
        "onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true)",
        "orientationControllerDelegate.isInitialized()",
        "recoveryDelegate.isInitialized()",
        "sourceSelectionControllerDelegate.isInitialized()",
    )
    missing = [token for token in required if token not in source]
    if missing:
        raise SystemExit("Faltan cambios de calidad del reproductor: " + ", ".join(missing))
    forbidden = ("!!", "intent.getParcelableExtra<Channel>", "override fun onBackPressed()")
    found = [token for token in forbidden if token in source]
    if found:
        raise SystemExit("Persisten patrones que debían eliminarse: " + ", ".join(found))
    if source.count("DeviceHelper.isTV(this)") != 1:
        raise SystemExit("La detección de dispositivo no quedó centralizada en una sola lectura.")
    keep_screen_on = "window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)"
    if source.count(keep_screen_on) != 1:
        raise SystemExit("La pantalla debe mantenerse activa con una única bandera en el reproductor.")
    create_start = source.index("    override fun onCreate(")
    create_end = source.index("\n    override fun onResume(", create_start)
    if keep_screen_on not in source[create_start:create_end]:
        raise SystemExit("FLAG_KEEP_SCREEN_ON debe configurarse en onCreate() para móvil y Android TV.")
    immersive_start = source.index("    private fun enableImmersiveFullscreen() {")
    webview_start = source.index("    // ==================== WEBVIEW", immersive_start)
    if keep_screen_on in source[immersive_start:webview_start]:
        raise SystemExit("FLAG_KEEP_SCREEN_ON no debe depender de la configuración inmersiva de móvil.")
    start = source.index("    private fun changeChannel(delta: Int) {")
    end = source.index("    private fun zapTo(index: Int, channel: Channel) {", start)
    change_channel = source[start:end]
    if change_channel.count("currentChannelIndex + delta") != 1:
        raise SystemExit("changeChannel todavía calcula más de una vez el índice circular.")
    if "if (isZapping) {\n            pendingZapAccumulator.accumulate(delta)" not in change_channel:
        raise SystemExit("changeChannel todavía descarta pulsaciones mientras hay zapping.")
    if "private fun dp(" in source:
        raise SystemExit("Se detectó una función dp() que no se utiliza.")
    print("Player quality regression checks: OK.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
