#!/usr/bin/env python3
"""Extract the Android TV navigation rail and remove obsolete inline handoff code."""
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1]).resolve()
LAYOUT = ROOT / "app/src/main/res/layout"
JAVA = ROOT / "app/src/main/java/com/angulismotv"


def write_if_changed(path: Path, content: str) -> None:
    if not path.exists() or path.read_text(encoding="utf-8") != content:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
        print("updated", path.relative_to(ROOT))


def extract_side_menu() -> None:
    main_path = LAYOUT / "activity_main.xml"
    side_path = LAYOUT / "view_tv_side_menu.xml"
    main = main_path.read_text(encoding="utf-8")
    if re.search(r'<include\b[^>]*layout="@layout/view_tv_side_menu"', main):
        if not side_path.exists():
            raise SystemExit("activity_main.xml incluye view_tv_side_menu, pero el layout no existe")
        return

    open_tag = re.compile(r'<LinearLayout\b(?=[^>]*android:id="@\+id/side_menu")[^>]*>')
    match = open_tag.search(main)
    if not match:
        raise SystemExit("No se encontró el LinearLayout @id/side_menu para extraer")

    # Cuenta aperturas/cierres de LinearLayout, sin confundir hijos anidados con el root.
    depth = 1
    end = None
    token_re = re.compile(r'</?LinearLayout\b[^>]*>')
    for token in token_re.finditer(main, match.end()):
        token_text = token.group(0)
        if token_text.startswith("</"):
            depth -= 1
            if depth == 0:
                end = token.end()
                break
        elif not token_text.rstrip().endswith("/>"):
            depth += 1
    if end is None:
        raise SystemExit("No se pudo encontrar el cierre de side_menu")

    menu_xml = main[match.start():end]
    # Los namespaces de activity_main.xml no se heredan al extraer un layout nuevo.
    root_open = re.search(r'<LinearLayout\b[^>]*>', menu_xml)
    assert root_open
    root_tag = root_open.group(0)
    if "xmlns:android=" not in root_tag:
        root_tag = root_tag[:-1] + ' xmlns:android="http://schemas.android.com/apk/res/android">'
    if "xmlns:app=" not in root_tag:
        root_tag = root_tag[:-1] + ' xmlns:app="http://schemas.android.com/apk/res-auto">'
    menu_xml = menu_xml[:root_open.start()] + root_tag + menu_xml[root_open.end():]
    write_if_changed(side_path, '<?xml version="1.0" encoding="utf-8"?>\n' + menu_xml + '\n')

    replacement = '<include layout="@layout/view_tv_side_menu" />'
    main = main[:match.start()] + replacement + main[end:]
    write_if_changed(main_path, main)


def decouple_main_activity_binding() -> None:
    path = JAVA / "MainActivity.kt"
    s = path.read_text(encoding="utf-8")
    marker = "    private lateinit var binding: ActivityMainBinding\n"
    properties = """    // El rail de TV vive en view_tv_side_menu.xml; su navegación permanece en esta Activity.
    private val sideMenu: LinearLayout by lazy(LazyThreadSafetyMode.NONE) { findViewById(R.id.side_menu) }
    private val menuChannels: LinearLayout by lazy(LazyThreadSafetyMode.NONE) { findViewById(R.id.menu_channels) }
    private val menuAgenda: LinearLayout by lazy(LazyThreadSafetyMode.NONE) { findViewById(R.id.menu_agenda) }
    private val menuChannelsText: TextView by lazy(LazyThreadSafetyMode.NONE) { findViewById(R.id.menu_channels_text) }
    private val menuAgendaText: TextView by lazy(LazyThreadSafetyMode.NONE) { findViewById(R.id.menu_agenda_text) }
"""
    if "private val sideMenu: LinearLayout by lazy" not in s:
        if marker not in s:
            raise SystemExit("No se encontró el campo binding de MainActivity.kt")
        s = s.replace(marker, marker + properties, 1)

    replacements = {
        "binding.sideMenu": "sideMenu",
        "binding.menuChannelsText": "menuChannelsText",
        "binding.menuAgendaText": "menuAgendaText",
        "binding.menuChannels": "menuChannels",
        "binding.menuAgenda": "menuAgenda",
    }
    for before, after in replacements.items():
        s = s.replace(before, after)
    write_if_changed(path, s)


def simplify_selected_background() -> None:
    path = ROOT / "app/src/main/res/drawable/bg_tv_rail_item.xml"
    s = path.read_text(encoding="utf-8")
    pat = re.compile(r'(<item\s+android:state_selected="true">.*?<solid\s+android:color=")[^"]+("\s*/>.*?</item>)', re.S)
    m = pat.search(s)
    if not m:
        raise SystemExit("No se encontró el estado seleccionado en bg_tv_rail_item.xml")
    new = m.group(1) + "#00000000" + m.group(2)
    s = s[:m.start()] + new + s[m.end():]
    write_if_changed(path, s)


def remove_legacy_handoff() -> None:
    path = JAVA / "fragments/ChannelsFragment.kt"
    s = path.read_text(encoding="utf-8")
    s, n_data = re.subn(
        r'private data class InlineHandoffPlan\(\s*val transferNativePlayer: Boolean,\s*val transferWebView: Boolean\s*\)\s*\n\s*',
        "", s, count=1
    )
    s, n_methods = re.subn(
        r'    private fun prepareInlineHandoff\(.*?(?=    private fun maybeOpenFullscreenAfterRotation\()',
        "", s, count=1, flags=re.S
    )
    if n_data == 0 and "private data class InlineHandoffPlan" in s:
        raise SystemExit("No se pudo retirar InlineHandoffPlan heredado")
    if n_methods == 0 and "private fun prepareInlineHandoff(" in s:
        raise SystemExit("No se pudo retirar el traspaso heredado")
    write_if_changed(path, s)


def update_design_doc() -> None:
    path = ROOT / "SISTEMA-DISENO-UI.md"
    if not path.exists():
        return
    s = path.read_text(encoding="utf-8")
    line = "- app/src/main/res/layout/view_tv_side_menu.xml: estructura del rail de navegación exclusivo de Android TV.\n"
    if line.strip() not in s:
        anchor = "- app/src/main/res/layout/: estructura de las pantallas; mantener referencias a tokens compartidos.\n"
        if anchor in s:
            s = s.replace(anchor, line + anchor, 1)
        else:
            s += "\n" + line
        write_if_changed(path, s)


def main() -> None:
    if not (ROOT / "settings.gradle.kts").exists():
        raise SystemExit(f"Not a Gradle Android root: {ROOT}")
    extract_side_menu()
    decouple_main_activity_binding()
    simplify_selected_background()
    remove_legacy_handoff()
    update_design_doc()
    print("TV side menu modularization and legacy handoff cleanup applied")


if __name__ == "__main__":
    main()
