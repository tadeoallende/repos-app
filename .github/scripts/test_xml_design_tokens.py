#!/usr/bin/env python3
"""Regression checks for shared XML dimensions in agenda, channel rows and side lists."""
from pathlib import Path
import re
import sys

root = Path(sys.argv[1]).resolve()
res = root / "app/src/main/res"
values = (res / "values/dimens.xml").read_text(encoding="utf-8")
layout = res / "layout"

required_dimensions = {
    "channel_row_padding_horizontal_mobile", "channel_row_padding_vertical_mobile",
    "channel_row_min_height_mobile", "channel_row_min_height_tv",
    "channel_row_margin_horizontal_tv", "channel_row_margin_vertical_tv",
    "channel_row_number_width", "channel_logo_size_mobile", "channel_logo_size_tv",
    "channel_row_logo_padding", "channel_row_name_margin_mobile", "channel_row_name_margin_tv",
    "channel_row_options_icon_size_mobile", "channel_row_options_icon_size_tv",
    "channel_row_options_margin_mobile", "channel_row_options_margin_tv",
    "channel_row_play_icon_size", "side_channel_row_min_height",
    "side_channel_row_padding_horizontal", "side_channel_row_padding_vertical",
    "side_channel_row_margin_horizontal", "side_channel_row_margin_vertical",
    "side_channel_marker_width", "side_channel_marker_height", "side_channel_marker_margin_end",
    "side_channel_number_width", "side_channel_logo_size", "side_channel_name_margin_start",
    "side_channel_options_icon_size", "side_channel_options_margin_start",
    "side_category_min_height", "side_category_padding_horizontal", "side_category_padding_vertical",
    "side_category_margin_horizontal", "side_category_margin_vertical", "side_category_marker_width",
    "side_category_marker_height", "side_category_marker_margin_end", "side_category_icon_size",
    "side_category_icon_margin_end", "side_category_count_margin_start",
    "side_category_count_min_width", "side_category_count_padding_horizontal",
    "agenda_progress_padding", "agenda_overlay_elevation", "agenda_error_margin",
    "agenda_error_padding_horizontal", "agenda_error_padding_vertical",
    "agenda_error_max_width", "agenda_error_text_size",
}
missing = sorted(name for name in required_dimensions if not re.search(r'<dimen\s+name="' + re.escape(name) + r'">', values))
if missing:
    raise SystemExit("FAIL: missing shared dimensions: " + ", ".join(missing))

checks = {
    "item_channel.xml": {
        "channel_item_root": ("android:paddingStart", "android:paddingEnd", "android:paddingTop", "android:paddingBottom", "android:minHeight"),
        "channel_logo": ("android:layout_width", "android:layout_height", "android:padding"),
        "channel_name": ("android:layout_marginStart",),
    },
    "item_channel_tv.xml": {
        "channel_item_root": ("android:minHeight", "android:layout_marginStart", "android:layout_marginTop"),
        "channel_logo": ("android:layout_width", "android:layout_height", "android:padding"),
        "channel_name": ("android:layout_marginStart",),
    },
    "item_channel_side.xml": {
        "channel_selected_marker": ("android:layout_width", "android:layout_height", "android:layout_marginEnd"),
        "channel_logo": ("android:layout_width", "android:layout_height"),
        "channel_name": ("android:layout_marginStart",),
    },
    "item_category_side.xml": {
        "category_selected_marker": ("android:layout_width", "android:layout_height", "android:layout_marginEnd"),
        "category_icon": ("android:layout_width", "android:layout_height", "android:layout_marginEnd"),
        "category_count": ("android:minWidth", "android:paddingStart", "android:paddingEnd"),
    },
    "fragment_agenda.xml": {
        "progress_bar": ("android:padding", "android:elevation"),
        "error_text": ("android:layout_margin", "android:paddingHorizontal", "android:paddingVertical", "android:maxWidth", "android:textSize"),
    },
}
for file, views in checks.items():
    source = (layout / file).read_text(encoding="utf-8")
    for view_id, attrs in views.items():
        match = re.search(r'<[A-Za-z][A-Za-z0-9.]*\b(?=[^>]*android:id="@\+id/' + re.escape(view_id) + r'")[^>]*>', source, re.S)
        if not match:
            raise SystemExit(f"FAIL: missing view {view_id} in {file}")
        tag = match.group(0)
        for attr in attrs:
            if not re.search(re.escape(attr) + r'="@dimen/', tag):
                raise SystemExit(f"FAIL: {file}#{view_id} must use a shared dimension for {attr}")

print("PASS: agenda and channel/sidebar layouts use shared dimension tokens")
