#!/usr/bin/env python3
"""Apply tracked source overlays to the Android project ZIP before GitHub Actions builds it."""
from __future__ import annotations
import os
from pathlib import Path
import sys
import tempfile
import zipfile


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: apply_zip_overrides.py <proyecto.zip>", file=sys.stderr)
        return 2
    archive = Path(sys.argv[1]).resolve()
    overlay_root = Path.cwd() / ".github" / "project-overrides"
    if not archive.is_file() or not zipfile.is_zipfile(archive):
        print(f"No es un ZIP válido: {archive}", file=sys.stderr)
        return 2
    if not overlay_root.is_dir():
        print(f"No existe el directorio de overlays: {overlay_root}", file=sys.stderr)
        return 2

    overlays = {
        path.relative_to(overlay_root).as_posix(): path.read_bytes()
        for path in overlay_root.rglob("*") if path.is_file()
    }
    if not overlays:
        print("No se encontraron archivos de overlay", file=sys.stderr)
        return 2

    fd, temp_name = tempfile.mkstemp(prefix=archive.stem + "-", suffix=".zip", dir=archive.parent)
    os.close(fd)
    temp = Path(temp_name)
    written: set[str] = set()
    try:
        with zipfile.ZipFile(archive, "r") as source, zipfile.ZipFile(
            temp, "w", compression=zipfile.ZIP_DEFLATED
        ) as target:
            for info in source.infolist():
                name = info.filename
                if name in overlays:
                    target.writestr(info, overlays[name])
                    written.add(name)
                else:
                    target.writestr(info, source.read(name))
            for name, content in overlays.items():
                if name not in written:
                    target.writestr(name, content, compress_type=zipfile.ZIP_DEFLATED)
                    written.add(name)
        os.replace(temp, archive)
    finally:
        if temp.exists():
            temp.unlink()

    with zipfile.ZipFile(archive, "r") as result:
        damaged_entry = result.testzip()
        if damaged_entry:
            raise SystemExit(f"ZIP dañado después de aplicar los overlays: {damaged_entry}")
    print(f"ZIP actualizado: {archive.name}; archivos aplicados: {len(overlays)}")
    for name in sorted(overlays):
        print(f"  - {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
