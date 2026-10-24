#!/usr/bin/env python3
"""Regression guard: Android TV must initialize channel numbers before rendering rows."""
from pathlib import Path
import re
import sys

root = Path(sys.argv[1]).resolve()
source_path = root / "app/src/main/java/com/angulismotv/fragments/ChannelsFragment.kt"
source = source_path.read_text(encoding="utf-8")

method = re.search(
    r"private fun generateCategoriesFromChannels\(channels: List<Channel>\) \{(.*?)"
    r"\n    \}\n\n    private fun selectCategory",
    source,
    re.S,
)
if not method:
    raise SystemExit("FAIL: generateCategoriesFromChannels could not be located")

tv_branch = re.search(r"if \(isTV\) \{(.*?)\n            return\n        \}", method.group(1), re.S)
if not tv_branch:
    raise SystemExit("FAIL: Android TV initialization branch could not be located")

body = tv_branch.group(1)
required_in_order = [
    "ChannelCatalog.channelNumbersByIdentity(channels)",
    "channelNumbersByIdentity = channelNumbers",
    "applyFiltersAndUpdate { restoreLastActiveChannel(channels) }",
]
positions = [body.find(fragment) for fragment in required_in_order]
if any(position < 0 for position in positions) or positions != sorted(positions):
    raise SystemExit(
        "FAIL: TV channel numbers must be calculated and published before the list is rendered"
    )
for guard in ("expectedViewGeneration != viewGeneration", "originalChannels !== channels"):
    if guard not in body:
        raise SystemExit(f"FAIL: stale TV catalog guard missing: {guard}")

print("PASS: Android TV initializes channel numbers before rendering channels")
