#!/usr/bin/env python3
"""Regression test for duplicate paths in ZIPs processed by apply_zip_overrides.py."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import zipfile


SCRIPT = Path(__file__).with_name("apply_zip_overrides.py")
SPEC = importlib.util.spec_from_file_location("apply_zip_overrides", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise SystemExit("No se pudo cargar apply_zip_overrides.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="zip-duplicate-test-") as tmp:
        archive = Path(tmp) / "duplicate.zip"
        with zipfile.ZipFile(archive, "w") as source:
            source.writestr("app/src/main/res/layout/sample.xml", "old-layout")
            source.writestr("keep.txt", "keep")
            source.writestr("app/src/main/res/layout/sample.xml", "new-layout")

        with zipfile.ZipFile(archive, "r") as source:
            infos = source.infolist()
            selected = MODULE.unique_archive_entries(infos)
            names = [info.filename for info in selected]
            assert names == ["keep.txt", "app/src/main/res/layout/sample.xml"], names
            selected_layout = next(
                info for info in selected
                if info.filename == "app/src/main/res/layout/sample.xml"
            )
            assert source.read(selected_layout).decode("utf-8") == "new-layout"

    print("ZIP duplicate-entry regression: OK (keeps the last entry for each path).")

    if len(sys.argv) > 1:
        actual_archive = Path(sys.argv[1])
        with zipfile.ZipFile(actual_archive, "r") as source:
            names = [info.filename for info in source.infolist()]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            raise SystemExit("El ZIP de compilación todavía tiene rutas duplicadas: " + ", ".join(duplicates[:20]))
        print(f"ZIP de compilación sin rutas duplicadas: {len(names)} entradas.")


if __name__ == "__main__":
    main()
