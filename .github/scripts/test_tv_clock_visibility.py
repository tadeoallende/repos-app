#!/usr/bin/env python3
"""Protect the explicit Android TV-only clock behavior."""
from pathlib import Path
import re
import sys

root = Path(sys.argv[1]).resolve()
activity = (root / "app/src/main/java/com/angulismotv/MainActivity.kt").read_text(encoding="utf-8")
layout = (root / "app/src/main/res/layout/activity_main.xml").read_text(encoding="utf-8")

tv = re.search(
    r"private fun setupTvHeader\(\) \{(.*?)(?=\n    private fun setupMobileHeader\(\))",
    activity, re.S
)
mobile = re.search(
    r"private fun setupMobileHeader\(\) \{(.*?)(?=\n    private fun )",
    activity, re.S
)
clock = re.search(r"<TextClock\b[^>]*android:id=\"@\+id/header_clock\"[^>]*>", layout)
if not tv or "binding.headerClock.visibility = View.VISIBLE" not in tv.group(1):
    raise SystemExit("FAIL: the clock must be explicitly enabled for Android TV")
if not mobile or "binding.headerClock.visibility = View.GONE" not in mobile.group(1):
    raise SystemExit("FAIL: the clock must be hidden in the mobile header")
if not clock or 'android:visibility="gone"' not in clock.group(0):
    raise SystemExit("FAIL: the clock must start hidden in the shared layout")

print("PASS: the clock is visible only in Android TV mode")
