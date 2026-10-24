#!/usr/bin/env python3
"""Temporary diagnostic helper for reviewing UnifiedPlayerActivity after ZIP overlays."""
from __future__ import annotations

from pathlib import Path
import re
import sys

TARGET = Path("app/src/main/java/com/angulismotv/UnifiedPlayerActivity.kt")
METHODS = (
    "changeChannel",
    "reloadCurrentTransmission",
    "updateWebViewControls",
    "updateIframeTransportControls",
    "showControls",
    "showControlsTemporarily",
    "onCreate",
    "onPause",
    "onStop",
    "onDestroy",
    "onBackPressed",
    "dp",
)


def method_blocks(source: str, name: str) -> list[tuple[int, str]]:
    declaration = re.compile(
        r"(?m)^    (?:(?:override|private|protected|internal|public|suspend|final|open)\s+)*"
        r"fun\s+" + re.escape(name) + r"\b[^\n]*(?:\n(?!    (?:override|private|protected|internal|public|suspend|final|open)\s+fun\b)[^\n]*)*"
    )
    result = []
    for match in declaration.finditer(source):
        block = match.group(0)
        start = match.start()
        next_method = re.search(
            r"(?m)^    (?:(?:override|private|protected|internal|public|suspend|final|open)\s+)*fun\s+\w+\b",
            source[match.end():]
        )
        if next_method:
            block += source[match.end():match.end() + next_method.start()]
        result.append((source.count("\n", 0, start) + 1, block.rstrip()))
    return result


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: inspect_unified_player.py <project-dir>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    path = root / TARGET
    if not path.is_file():
        raise SystemExit(f"No se encontró {TARGET} en {root}")
    source = path.read_text(encoding="utf-8")
    is_tv_mentions = len(re.findall(r"\bisTV\b", source))
    dp_declaration = len(re.findall(r"(?m)^\s*(?:(?:private|protected|internal|public)\s+)?fun\s+dp\s*\(", source))
    dp_calls = len(re.findall(r"(?<![\w.])dp\s*\(", source))
    print("PLAYER_AUDIT_METRICS")
    print(f"non_null_assertions={source.count('!!')}")
    print(f"isTV_mentions={is_tv_mentions}")
    print(f"dp_declaration={dp_declaration}")
    print(f"dp_call_like={dp_calls}")
    print(f"getParcelableExtra_mentions={source.count('getParcelableExtra')}")
    print(f"self_assignment_currentStreamUrl={source.count('currentStreamUrl = url')}")
    print(f"self_assignment_currentStreamType={source.count('currentStreamType = type')}")
    print(f"source_lines={len(source.splitlines())}")
    lines = source.splitlines()
    context_terms = (
        "zapRunnable", "clearZappingRunnable", "hideZappingRunnable", "zappingOverlay",
        "isZapping", "currentChannelIndex", "sourceSelectionController", "orientationController",
        "recovery by lazy", "sourceSelectionController by lazy", "orientationController by lazy",
        "getParcelableExtra", "!!", "onBackPressedDispatcher", "onBackPressed"
    )
    print("\\n===== CONTEXT LINES =====")
    for line_number, line in enumerate(lines, 1):
        if any(term in line for term in context_terms):
            print(f"{line_number}: {line.rstrip()}")
    for name in ("zapTo", "clearZapping", "hideZapping", "onKeyDown", "onKeyUp", "handleBack"):
        for line_number, block in method_blocks(source, name):
            print(f"\\n===== EXTRA METHOD {name} at {line_number} =====")
            print(block)
    for name in METHODS:
        blocks = method_blocks(source, name)
        print(f"\n===== METHOD {name}: {len(blocks)} match(es) =====")
        for index, (line, block) in enumerate(blocks, 1):
            lines = block.splitlines()
            if len(lines) > 45:
                lines = lines[:45] + [f"... [{len(block.splitlines()) - 45} lines omitted] ..."]
            print(f"--- occurrence {index}; line {line} ---")
            print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
