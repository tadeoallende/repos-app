#!/usr/bin/env python3
"""Create shared UI design tokens and apply them to the selected AngulismoTV project."""
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1]).resolve()
V = ROOT / "app/src/main/res/values"
L = ROOT / "app/src/main/res/layout"
J = ROOT / "app/src/main/java/com/angulismotv"
U = J / "ui"


def read(p):
    return p.read_text(encoding="utf-8")


def write(p, s):
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists() or read(p) != s:
        p.write_text(s, encoding="utf-8", newline="\n")
        print("updated", p.relative_to(ROOT))


def append_resources(path, marker, block):
    s = read(path)
    if marker not in s:
        s = s.replace("</resources>", "\n" + block + "\n</resources>")
        write(path, s)


def token_dimensions():
    block = """    <!-- Shared AngulismoTV design tokens -->
    <dimen name="spacing_xs">4dp</dimen><dimen name="spacing_sm">8dp</dimen>
    <dimen name="spacing_md">12dp</dimen><dimen name="spacing_lg">16dp</dimen>
    <dimen name="spacing_xl">24dp</dimen><dimen name="spacing_2xl">32dp</dimen>
    <dimen name="text_size_micro">10sp</dimen><dimen name="text_size_caption">12sp</dimen>
    <dimen name="text_size_label">13sp</dimen><dimen name="text_size_body">14sp</dimen>
    <dimen name="text_size_section">16sp</dimen><dimen name="text_size_screen_title">24sp</dimen>
    <dimen name="text_size_header_clock">18sp</dimen><dimen name="text_size_channel_name_tv">15sp</dimen>
    <dimen name="text_size_player_time">9sp</dimen>
    <dimen name="header_height_mobile">48dp</dimen>
    <dimen name="tv_navigation_rail_collapsed_width">72dp</dimen><dimen name="tv_navigation_rail_expanded_width">232dp</dimen>
    <dimen name="header_logo_width">164dp</dimen><dimen name="header_logo_height_tv">42dp</dimen>
    <dimen name="header_logo_height_mobile">30dp</dimen><dimen name="header_logo_margin_start_tv">24dp</dimen>
    <dimen name="header_logo_margin_start_mobile">12dp</dimen><dimen name="header_search_button_size_mobile">44dp</dimen>
    <dimen name="header_search_button_size_tv">48dp</dimen><dimen name="header_search_button_margin_end_tv">12dp</dimen>
    <dimen name="header_search_button_padding_mobile">11dp</dimen>
    <dimen name="category_chip_height_mobile">36dp</dimen><dimen name="category_chip_height_tv">38dp</dimen>
    <dimen name="category_chip_text_size">13sp</dimen><dimen name="category_chip_padding_horizontal_mobile">12dp</dimen>
    <dimen name="category_chip_padding_horizontal_tv">16dp</dimen><dimen name="category_country_chip_padding_horizontal_tv">12dp</dimen>
    <dimen name="category_chip_margin_end_tv">8dp</dimen><dimen name="category_chip_margin_end_mobile">5dp</dimen>
    <dimen name="channels_search_padding_tv">4dp</dimen><dimen name="channels_search_padding_mobile">8dp</dimen>
    <dimen name="channels_search_padding_top_mobile">3dp</dimen><dimen name="channels_search_padding_bottom_mobile">2dp</dimen>
    <dimen name="channels_categories_padding_tv">4dp</dimen><dimen name="channels_categories_padding_horizontal_mobile">8dp</dimen>
    <dimen name="channels_categories_padding_vertical_mobile">2dp</dimen><dimen name="channels_recycler_padding_horizontal_tv">2dp</dimen>
    <dimen name="channels_recycler_padding_top_tv">4dp</dimen><dimen name="channels_recycler_padding_bottom_tv">6dp</dimen>
    <dimen name="channels_recycler_padding_horizontal_mobile">4dp</dimen><dimen name="channels_recycler_padding_top_mobile">1dp</dimen>
    <dimen name="channels_recycler_padding_bottom_mobile">8dp</dimen><dimen name="search_field_height_tv">46dp</dimen>
    <dimen name="search_field_height_mobile">44dp</dimen><dimen name="search_field_text_size_tv">15sp</dimen>
    <dimen name="search_field_text_size_mobile">14sp</dimen><dimen name="search_field_padding_horizontal">12dp</dimen>
    <dimen name="search_field_margin_start">8dp</dimen><dimen name="inline_player_container_margin_mobile">2dp</dimen>
    <dimen name="inline_controls_min_height">44dp</dimen><dimen name="inline_controls_padding_horizontal">6dp</dimen>
    <dimen name="inline_controls_padding_vertical">2dp</dimen><dimen name="inline_channel_logo_size_mobile">28dp</dimen>
    <dimen name="inline_channel_name_margin_start_mobile">6dp</dimen><dimen name="inline_channel_name_text_size_mobile">12sp</dimen>
    <dimen name="inline_timeline_height_mobile">24dp</dimen><dimen name="inline_timeline_margin_horizontal_mobile">8dp</dimen>
    <dimen name="inline_timeline_margin_bottom_mobile">46dp</dimen><dimen name="inline_timeline_time_width_mobile">32dp</dimen>
    <dimen name="inline_seekbar_height_mobile">20dp</dimen><dimen name="inline_player_primary_action_size">58dp</dimen>
    <dimen name="inline_player_primary_action_padding">17dp</dimen><dimen name="player_primary_action_size">48dp</dimen>
    <dimen name="player_primary_action_padding">12dp</dimen><dimen name="player_control_spacing_compact">8dp</dimen>
    <dimen name="player_control_spacing_regular">12dp</dimen><dimen name="player_controls_horizontal_padding_compact">16dp</dimen>
    <dimen name="player_controls_horizontal_padding_wide">22dp</dimen><dimen name="player_controls_padding_top">10dp</dimen>
    <dimen name="player_controls_padding_bottom">12dp</dimen><dimen name="player_control_size_tv">48dp</dimen>
    <dimen name="zapping_label_max_width_mobile">220dp</dimen><dimen name="zapping_label_max_width_tv">480dp</dimen>
"""
    append_resources(V / "dimens.xml", "Shared AngulismoTV design tokens", block)
    p = V / "dimens.xml"
    s = read(p)
    extra_dimensions = (
        '<dimen name="channel_logo_corner_radius_mobile">6dp</dimen>',
        '<dimen name="channel_logo_corner_radius_tv">12dp</dimen>',
        '<dimen name="player_loading_indicator_size">48dp</dimen>',
        '<dimen name="header_search_button_margin_end_mobile">0dp</dimen>',
        '<dimen name="inline_controls_scrim_height_mobile">96dp</dimen>',
        '<dimen name="player_error_padding">18dp</dimen>',
        '<dimen name="player_error_max_width">420dp</dimen>',
        '<dimen name="text_size_channel_number_overlay">32sp</dimen>',
        '<dimen name="zapping_overlay_margin">24dp</dimen>',
        '<dimen name="zapping_logo_size">52dp</dimen>',
        '<dimen name="zapping_label_margin_start">12dp</dimen>',
        '<dimen name="text_size_zapping_channel_name">22sp</dimen>',
        '<dimen name="player_timeline_height">30dp</dimen>',
        '<dimen name="player_timeline_time_width">48dp</dimen>',
        '<dimen name="player_timeline_seekbar_height">24dp</dimen>',
        '<dimen name="player_timeline_text_size">11sp</dimen>',
        '<dimen name="player_channel_logo_size">46dp</dimen>',
        '<dimen name="player_transport_button_gap">8dp</dimen>',
        '<dimen name="player_utility_button_gap">4dp</dimen>',
        '<dimen name="header_height_tv">64dp</dimen>',
        '<dimen name="header_container_elevation">4dp</dimen>',
        '<dimen name="bottom_navigation_elevation">2dp</dimen>',
        '<dimen name="navigation_rail_elevation">4dp</dimen>',
        '<dimen name="tv_navigation_rail_item_height">56dp</dimen>',
        '<dimen name="tv_navigation_rail_item_margin_horizontal">8dp</dimen>',
        '<dimen name="tv_navigation_rail_item_gap">6dp</dimen>',
        '<dimen name="tv_navigation_rail_item_label_padding_end">16dp</dimen>',
        '<dimen name="text_size_navigation_label">15sp</dimen>',
        '<dimen name="inline_player_loading_indicator_size">36dp</dimen>',
        '<dimen name="inline_player_error_margin">20dp</dimen>',
        '<dimen name="inline_player_error_padding">10dp</dimen>',
        '<dimen name="inline_player_error_text_size_mobile">12sp</dimen>',
        '<dimen name="inline_player_error_text_size_tv">14sp</dimen>',
        '<dimen name="text_size_tv_player_empty_title">20sp</dimen>',
        '<dimen name="inline_timeline_height_tv">24dp</dimen>',
        '<dimen name="inline_timeline_margin_horizontal_tv">8dp</dimen>',
        '<dimen name="inline_timeline_margin_bottom_tv">46dp</dimen>',
        '<dimen name="inline_timeline_padding_horizontal_tv">7dp</dimen>',
        '<dimen name="inline_timeline_time_width_tv">40dp</dimen>',
        '<dimen name="inline_timeline_text_size_tv">11sp</dimen>',
        '<dimen name="inline_seekbar_height_tv">20dp</dimen>',
        '<dimen name="inline_controls_padding_horizontal_tv">6dp</dimen>',
        '<dimen name="inline_channel_logo_size_tv">28dp</dimen>',
        '<dimen name="inline_channel_name_text_size_tv">14sp</dimen>',
        '<dimen name="tv_current_channel_info_padding_horizontal">16dp</dimen>',
        '<dimen name="tv_current_channel_info_padding_top">28dp</dimen>',
        '<dimen name="tv_current_channel_info_padding_bottom">12dp</dimen>',
        '<dimen name="tv_channels_search_panel_width">320dp</dimen>',
        '<dimen name="tv_channels_search_elevation">9dp</dimen>',
        '<dimen name="channels_search_icon_size">20dp</dimen>',
        '<dimen name="tv_player_action_row_margin_top">10dp</dimen>',
        '<dimen name="tv_player_action_row_padding_horizontal">2dp</dimen>',
        '<dimen name="tv_player_action_button_padding">12dp</dimen>',
        '<dimen name="tv_player_action_button_margin_end">10dp</dimen>',
        '<dimen name="tv_channels_section_title_text_size">21sp</dimen>',
        '<dimen name="tv_channels_subtitle_margin_top">2dp</dimen>',
        '<dimen name="tv_channels_scroll_hint_height">18dp</dimen>',
        '<dimen name="channels_error_text_size">15sp</dimen>',
        '<dimen name="inline_timeline_padding_horizontal_mobile">7dp</dimen>',
        '<dimen name="channels_section_header_padding_horizontal_mobile">12dp</dimen>',
        '<dimen name="channels_section_header_padding_bottom_mobile">2dp</dimen>',
    )
    missing_dimensions = [value for value in extra_dimensions if value.split('"')[1] not in s]
    if missing_dimensions:
        s = s.replace("</resources>", "\n    " + "\n    ".join(missing_dimensions) + "\n</resources>")
        write(p, s)


def component_styles():
    p = V / "styles.xml"
    if not p.exists() or "Widget.AngulismoTV.PlayerActionButton" not in read(p):
        s = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="TextAppearance.AngulismoTV.Body" parent="TextAppearance.MaterialComponents.Body1">
        <item name="android:fontFamily">sans-serif</item><item name="android:textSize">@dimen/text_size_body</item><item name="android:textColor">@color/text_primary</item>
    </style>
    <style name="TextAppearance.AngulismoTV.BodySecondary" parent="TextAppearance.MaterialComponents.Body2">
        <item name="android:fontFamily">sans-serif</item><item name="android:textSize">@dimen/text_size_body</item><item name="android:textColor">@color/text_secondary</item>
    </style>
    <style name="TextAppearance.AngulismoTV.Caption" parent="TextAppearance.MaterialComponents.Caption">
        <item name="android:fontFamily">sans-serif</item><item name="android:textSize">@dimen/text_size_caption</item><item name="android:textColor">@color/text_secondary</item>
    </style>
    <style name="TextAppearance.AngulismoTV.ChannelName" parent="TextAppearance.MaterialComponents.Body2">
        <item name="android:fontFamily">sans-serif-medium</item><item name="android:textSize">@dimen/text_size_body</item><item name="android:textColor">@color/text_primary</item><item name="android:letterSpacing">0.005</item>
    </style>
    <style name="TextAppearance.AngulismoTV.ChannelName.TV" parent="@style/TextAppearance.AngulismoTV.ChannelName"><item name="android:textSize">@dimen/text_size_channel_name_tv</item></style>
    <style name="TextAppearance.AngulismoTV.ChannelName.RowMobile" parent="@style/TextAppearance.AngulismoTV.ChannelName"><item name="android:textSize">@dimen/text_size_body</item><item name="android:letterSpacing">0</item></style>
    <style name="TextAppearance.AngulismoTV.ChannelName.RowTV" parent="@style/TextAppearance.AngulismoTV.ChannelName.TV"><item name="android:letterSpacing">0</item></style>
    <style name="TextAppearance.AngulismoTV.CategoryName" parent="@style/TextAppearance.AngulismoTV.ChannelName"><item name="android:textSize">@dimen/text_size_body</item></style>
    <style name="TextAppearance.AngulismoTV.CategoryCount" parent="TextAppearance.MaterialComponents.Caption">
        <item name="android:fontFamily">sans-serif-medium</item><item name="android:textSize">@dimen/text_size_caption</item><item name="android:textColor">@color/text_secondary</item>
    </style>
    <style name="TextAppearance.AngulismoTV.ChannelNumber" parent="TextAppearance.MaterialComponents.Caption">
        <item name="android:fontFamily">sans-serif-medium</item><item name="android:textSize">@dimen/text_size_caption</item><item name="android:textColor">@color/text_secondary</item><item name="android:includeFontPadding">false</item>
    </style>
    <style name="TextAppearance.AngulismoTV.PlayerTime" parent="TextAppearance.MaterialComponents.Caption">
        <item name="android:fontFamily">sans-serif-medium</item><item name="android:textSize">@dimen/text_size_player_time</item><item name="android:textColor">@color/text_primary</item>
    </style>
    <style name="TextAppearance.AngulismoTV.HeaderClock" parent="TextAppearance.MaterialComponents.Subtitle1">
        <item name="android:fontFamily">sans-serif-medium</item><item name="android:textSize">@dimen/text_size_header_clock</item><item name="android:textColor">@color/text_primary</item>
    </style>
    <style name="Widget.AngulismoTV.PlayerActionButton" parent="Widget.AppCompat.ImageButton">
        <item name="android:background">@drawable/control_button_bg_small</item><item name="android:padding">@dimen/player_action_padding</item><item name="android:scaleType">fitCenter</item>
    </style>
    <style name="Widget.AngulismoTV.PlayerTransportButton" parent="Widget.AppCompat.ImageButton">
        <item name="android:background">@drawable/control_button_bg</item><item name="android:padding">@dimen/player_action_padding</item><item name="android:scaleType">fitCenter</item>
    </style>
    <style name="Widget.AngulismoTV.PlayerPrimaryButton" parent="Widget.AppCompat.ImageButton">
        <item name="android:background">@drawable/play_button_bg</item><item name="android:padding">@dimen/player_primary_action_padding</item><item name="android:scaleType">fitCenter</item>
    </style>
    <style name="Widget.AngulismoTV.InlinePlayerActionButton" parent="Widget.AppCompat.ImageButton">
        <item name="android:background">@drawable/bg_inline_player_control</item><item name="android:padding">@dimen/inline_player_icon_padding</item><item name="android:scaleType">fitCenter</item>
    </style>
    <style name="Widget.AngulismoTV.InlinePlayerPrimaryButton" parent="@style/Widget.AngulismoTV.PlayerPrimaryButton"><item name="android:padding">@dimen/inline_player_primary_action_padding</item></style>
    <style name="Widget.AngulismoTV.HeaderIconButton" parent="@style/Widget.AngulismoTV.InlinePlayerActionButton"><item name="android:padding">@dimen/header_search_button_padding_mobile</item></style>
    <style name="Widget.AngulismoTV.CategoryChip" parent="Widget.AppCompat.TextView">
        <item name="android:paddingHorizontal">@dimen/category_chip_padding_horizontal_mobile</item><item name="android:gravity">center</item><item name="android:textSize">@dimen/category_chip_text_size</item>
        <item name="android:fontFamily">sans-serif-medium</item><item name="android:letterSpacing">0.005</item><item name="android:singleLine">true</item><item name="android:ellipsize">end</item>
        <item name="android:textColor">@color/category_chip_text_selector</item><item name="android:background">@drawable/bg_category_chip_selector</item>
    </style>
</resources>
"""
        write(p, s)

    # Keep existing public TextAppearance names and move their sizes to shared tokens.
    p = V / "themes.xml"
    s = read(p)
    for name, old, new in [
        ("TextAppearance.AngulismoTV.ScreenTitle", "24sp", "@dimen/text_size_screen_title"),
        ("TextAppearance.AngulismoTV.ScreenSubtitle", "14sp", "@dimen/text_size_body"),
        ("TextAppearance.AngulismoTV.BottomNavigation.Active", "12sp", "@dimen/text_size_caption"),
        ("TextAppearance.AngulismoTV.BottomNavigation.Inactive", "12sp", "@dimen/text_size_caption"),
    ]:
        pat = re.compile(r'(<style name="' + re.escape(name) + r'"[^>]*>.*?</style>)', re.S)
        m = pat.search(s)
        if m:
            block = m.group(1).replace(f'<item name="android:textSize">{old}</item>', f'<item name="android:textSize">{new}</item>')
            s = s[:m.start(1)] + block + s[m.end(1):]
    write(p, s)



    # Ensure these component tokens exist even when styles.xml predates the current generator.
    p = V / "styles.xml"
    s = read(p)
    row_styles = """    <style name="TextAppearance.AngulismoTV.ChannelName.RowMobile" parent="@style/TextAppearance.AngulismoTV.ChannelName"><item name="android:textSize">@dimen/text_size_body</item><item name="android:letterSpacing">0</item></style>
    <style name="TextAppearance.AngulismoTV.ChannelName.RowTV" parent="@style/TextAppearance.AngulismoTV.ChannelName.TV"><item name="android:letterSpacing">0</item></style>"""
    if "TextAppearance.AngulismoTV.ChannelName.RowMobile" not in s:
        s = s.replace("</resources>", row_styles + "\n</resources>")
    category_pattern = re.compile(r'(<style name="Widget\.AngulismoTV\.CategoryChip"[^>]*>)(.*?)(</style>)', re.S)
    match = category_pattern.search(s)
    if not match:
        raise SystemExit("Missing Widget.AngulismoTV.CategoryChip style")
    category_body = match.group(2)
    category_body = re.sub(
        r'<item name="android:textColor">.*?</item>',
        '<item name="android:textColor">@color/category_chip_text_selector</item>',
        category_body, count=1
    )
    category_body = re.sub(
        r'<item name="android:background">.*?</item>',
        '<item name="android:background">@drawable/bg_category_chip_selector</item>',
        category_body, count=1
    )
    s = s[:match.start()] + match.group(1) + category_body + match.group(3) + s[match.end():]
    write(p, s)

def style_view(path, view_id, attr, style, remove=()):
    s = read(path)
    pat = re.compile(r'<(?P<tag>[\w.:]+)\b(?P<attrs>[^>]*\bandroid:id="@\+id/' + re.escape(view_id) + r'"[^>]*)>', re.S)
    m = pat.search(s)
    if not m:
        if f'android:id="@+id/{view_id}"' in s and f'{attr}="@style/{style}"' in s:
            return
        raise SystemExit(f"Missing view {view_id} in {path}")
    tag = m.group(0)
    if f'{attr}="@style/{style}"' not in tag:
        tag = re.sub(r'(<[\w.:]+\b)', r'\1 ' + attr + '="@style/' + style + '"', tag, count=1)
    for a in remove:
        tag = re.sub(r'\s+' + re.escape(a) + r'="[^"]*"', '', tag)
    write(path, s[:m.start()] + tag + s[m.end():])


def set_view_attributes(path, updates):
    """Move fixed visual dimensions for selected views into shared dimen resources."""
    s = read(path)
    for view_id, attributes in updates.items():
        pat = re.compile(
            r'<(?P<tag>[\w.:]+\b[^>]*\bandroid:id="@\+id/' + re.escape(view_id) + r'"[^>]*)>',
            re.S
        )
        match = pat.search(s)
        if not match:
            raise SystemExit(f"Missing view {view_id} in {path}")
        tag = match.group(0)
        for attr, value in attributes.items():
            attr_pat = re.compile(r'(?<![\w:])' + re.escape(attr) + r'="[^"]*"')
            tag, count = attr_pat.subn(lambda _: f'{attr}="{value}"', tag, count=1)
            if count == 0 and attr == "android:visibility":
                # A layout may rely on the Android default; visibility is safe to make explicit.
                if tag.endswith("/>"):
                    tag = tag[:-2] + f' {attr}="{value}" />'
                else:
                    tag = tag[:-1] + f' {attr}="{value}">'
                continue
            if count != 1:
                raise SystemExit(f"Missing attribute {attr} on {view_id} in {path}")
        s = s[:match.start()] + tag + s[match.end():]
    write(path, s)


def update_xml():
    style_view(L / "item_category.xml", "category_chip", "style", "Widget.AngulismoTV.CategoryChip", (
        "android:paddingHorizontal", "android:gravity", "android:textSize", "android:fontFamily", "android:letterSpacing", "android:singleLine", "android:ellipsize", "android:textColor", "android:background"))
    p = L / "item_category.xml"
    s = read(p).replace('android:layout_height="36dp"', 'android:layout_height="@dimen/category_chip_height_mobile"')
    s = s.replace('android:layout_marginEnd="5dp"', 'android:layout_marginEnd="@dimen/category_chip_margin_end_mobile"')
    write(p, s)

    for file, view, style in [
        ("item_channel.xml", "channel_number", "TextAppearance.AngulismoTV.ChannelNumber"),
        ("item_channel.xml", "channel_name", "TextAppearance.AngulismoTV.ChannelName.RowMobile"),
        ("item_channel_tv.xml", "channel_number", "TextAppearance.AngulismoTV.ChannelNumber"),
        ("item_channel_tv.xml", "channel_name", "TextAppearance.AngulismoTV.ChannelName.RowTV"),
        ("item_channel_side.xml", "channel_number", "TextAppearance.AngulismoTV.ChannelNumber"),
        ("item_channel_side.xml", "channel_name", "TextAppearance.AngulismoTV.ChannelName.TV"),
        ("item_category_side.xml", "category_name", "TextAppearance.AngulismoTV.CategoryName"),
        ("item_category_side.xml", "category_count", "TextAppearance.AngulismoTV.CategoryCount"),
    ]:
        style_view(L / file, view, "android:textAppearance", style,
                   ("android:textColor", "android:textSize", "android:fontFamily", "android:letterSpacing", "android:includeFontPadding"))

    p = L / "activity_unified_player.xml"
    for view in ("btn_menu", "media_route_button", "btn_options", "btn_favorite_channel", "btn_reload_stream", "btn_close_player"):
        style_view(p, view, "style", "Widget.AngulismoTV.PlayerActionButton", ("android:background", "android:padding"))
    for view in ("btn_rewind", "btn_forward"):
        style_view(p, view, "style", "Widget.AngulismoTV.PlayerTransportButton", ("android:background", "android:padding"))
    style_view(p, "btn_play_pause", "style", "Widget.AngulismoTV.PlayerPrimaryButton", ("android:background", "android:padding"))
    set_view_attributes(p, {
        "progress_bar": {
            "android:layout_width": "@dimen/player_loading_indicator_size",
            "android:layout_height": "@dimen/player_loading_indicator_size",
        },
        "error_text": {
            "android:padding": "@dimen/player_error_padding",
            "android:maxWidth": "@dimen/player_error_max_width",
            "android:textSize": "@dimen/text_size_section",
        },
        "channel_number_overlay": {
            "android:textSize": "@dimen/text_size_channel_number_overlay",
        },
        "zapping_overlay": {
            "android:layout_marginStart": "@dimen/zapping_overlay_margin",
            "android:layout_marginTop": "@dimen/zapping_overlay_margin",
        },
        "zapping_logo": {
            "android:layout_width": "@dimen/zapping_logo_size",
            "android:layout_height": "@dimen/zapping_logo_size",
        },
        "zapping_channel_name": {
            "android:layout_marginStart": "@dimen/zapping_label_margin_start",
            "android:maxWidth": "@dimen/zapping_label_max_width_tv",
            "android:textSize": "@dimen/text_size_zapping_channel_name",
        },
        "bottom_controls": {
            "android:paddingStart": "@dimen/player_controls_horizontal_padding_wide",
            "android:paddingEnd": "@dimen/player_controls_horizontal_padding_wide",
            "android:paddingTop": "@dimen/player_controls_padding_top",
            "android:paddingBottom": "@dimen/player_controls_padding_bottom",
        },
        "player_remote_help": {
            "android:layout_marginBottom": "@dimen/spacing_sm",
            "android:textSize": "@dimen/text_size_caption",
        },
        "player_timeline_container": {
            "android:layout_height": "@dimen/player_timeline_height",
            "android:layout_marginBottom": "@dimen/player_control_spacing_compact",
        },
        "player_time_current": {
            "android:layout_width": "@dimen/player_timeline_time_width",
            "android:textSize": "@dimen/player_timeline_text_size",
        },
        "player_seek_bar": {
            "android:layout_height": "@dimen/player_timeline_seekbar_height",
        },
        "player_time_duration": {
            "android:layout_width": "@dimen/player_timeline_time_width",
            "android:textSize": "@dimen/player_timeline_text_size",
        },
        "channel_logo": {
            "android:layout_width": "@dimen/player_channel_logo_size",
            "android:layout_height": "@dimen/player_channel_logo_size",
        },
        "channel_name": {
            "android:textSize": "@dimen/text_size_section",
        },
        "channel_category": {
            "android:layout_marginTop": "@dimen/spacing_xs",
            "android:textSize": "@dimen/text_size_caption",
        },
        "player_transport_controls": {
            "android:layout_marginStart": "@dimen/player_control_spacing_regular",
        },
        "btn_rewind": {
            "android:layout_marginEnd": "@dimen/player_transport_button_gap",
        },
        "btn_play_pause": {
            "android:layout_width": "@dimen/player_primary_action_size",
            "android:layout_height": "@dimen/player_primary_action_size",
            "android:layout_marginEnd": "@dimen/player_transport_button_gap",
        },
        "player_utility_controls": {
            "android:layout_marginStart": "@dimen/player_control_spacing_regular",
        },
        "btn_menu": {
            "android:layout_marginEnd": "@dimen/player_utility_button_gap",
        },
        "media_route_button": {
            "android:layout_marginEnd": "@dimen/player_utility_button_gap",
        },
        "btn_options": {
            "android:layout_marginEnd": "@dimen/player_utility_button_gap",
        },
        "btn_favorite_channel": {
            "android:layout_marginEnd": "@dimen/player_utility_button_gap",
        },
        "btn_reload_stream": {
            "android:layout_marginEnd": "@dimen/player_utility_button_gap",
        },
    })

    # Contenedor independiente para los controles de transporte en el centro del video móvil.
    p = L / "activity_unified_player.xml"
    s = read(p)
    if "center_transport_controls_container" not in s:
        match = re.search(r'(?P<indent> *)<LinearLayout\b(?=[^>]*android:id="@\+id/bottom_controls")', s)
        if not match:
            raise SystemExit("Missing bottom_controls in activity_unified_player.xml")
        indent = match.group("indent")
        center_controls = (
            indent + '<FrameLayout android:id="@+id/center_transport_controls_container" '
            'android:layout_width="match_parent" android:layout_height="match_parent" '
            'android:layout_gravity="center" android:visibility="gone" '
            'android:clickable="false" android:focusable="false" />\n'
        )
        s = s[:match.start()] + center_controls + s[match.start():]
        write(p, s)

    mobile = L / "fragment_channels.xml"
    style_view(mobile, "inline_btn_play_pause", "style", "Widget.AngulismoTV.InlinePlayerPrimaryButton", ("android:background", "android:padding"))
    s = read(mobile).replace('android:layout_width="58dp"', 'android:layout_width="@dimen/inline_player_primary_action_size"').replace('android:layout_height="58dp"', 'android:layout_height="@dimen/inline_player_primary_action_size"')
    write(mobile, s)
    for p in (mobile, L / "fragment_channels_tv.xml"):
        for view in ("inline_btn_reload", "inline_btn_sources", "inline_btn_cast", "inline_btn_fullscreen", "inline_btn_close"):
            style_view(p, view, "style", "Widget.AngulismoTV.InlinePlayerActionButton", ("android:background", "android:padding"))
        if p.name == "fragment_channels_tv.xml":
            style_view(p, "inline_btn_play_pause", "style", "Widget.AngulismoTV.InlinePlayerActionButton", ("android:background", "android:padding"))
    main = L / "activity_main.xml"
    style_view(main, "header_search_button", "style", "Widget.AngulismoTV.HeaderIconButton", ("android:background", "android:padding"))
    s = read(main).replace('android:layout_width="44dp" android:layout_height="44dp"', 'android:layout_width="@dimen/header_search_button_size_mobile" android:layout_height="@dimen/header_search_button_size_mobile"')
    s = re.sub(r'(<TextClock\b(?=[^>]*android:id="@\+id/header_clock")[^>]*?)\s+android:textColor="[^"]*"\s+android:textSize="[^"]*"\s+android:fontFamily="[^"]*"', r'\1 android:textAppearance="@style/TextAppearance.AngulismoTV.HeaderClock"', s, count=1)
    write(main, s)
    # El reloj está en la jerarquía común, pero arranca oculto: solo el modo TV lo habilita.
    set_view_attributes(main, {
        "header_search_button": {"android:layout_marginEnd": "@dimen/header_search_button_margin_end_mobile"},
        "header_clock": {"android:visibility": "gone"},
    })


    # Centraliza las medidas de la cabecera y la navegación sin alterar su geometría.
    main = L / "activity_main.xml"
    set_view_attributes(main, {
        "main_container": {
            "android:layout_marginStart": "@dimen/tv_navigation_rail_collapsed_width",
            "android:layout_marginTop": "@dimen/header_height_tv",
        },
        "bottom_navigation": {
            "android:layout_height": "@dimen/bottom_nav_height",
            "android:elevation": "@dimen/bottom_navigation_elevation",
        },
        "header_container": {
            "android:layout_height": "@dimen/header_height_tv",
            "android:elevation": "@dimen/header_container_elevation",
        },
        "logo_image": {
            "android:layout_width": "@dimen/header_logo_width",
            "android:layout_height": "@dimen/header_logo_height_tv",
            "android:layout_marginStart": "@dimen/header_logo_margin_start_tv",
        },
        "side_menu": {
            "android:layout_width": "@dimen/tv_navigation_rail_collapsed_width",
            "android:layout_marginTop": "@dimen/header_height_tv",
            "android:elevation": "@dimen/navigation_rail_elevation",
        },
        "menu_channels": {
            "android:layout_height": "@dimen/tv_navigation_rail_item_height",
            "android:layout_marginHorizontal": "@dimen/tv_navigation_rail_item_margin_horizontal",
        },
        "menu_agenda": {
            "android:layout_height": "@dimen/tv_navigation_rail_item_height",
            "android:layout_marginHorizontal": "@dimen/tv_navigation_rail_item_margin_horizontal",
            "android:layout_marginTop": "@dimen/tv_navigation_rail_item_gap",
        },
        "menu_channels_text": {
            "android:paddingEnd": "@dimen/tv_navigation_rail_item_label_padding_end",
            "android:textSize": "@dimen/text_size_navigation_label",
        },
        "menu_agenda_text": {
            "android:paddingEnd": "@dimen/tv_navigation_rail_item_label_padding_end",
            "android:textSize": "@dimen/text_size_navigation_label",
        },
    })

    tv = L / "fragment_channels_tv.xml"
    set_view_attributes(tv, {
        "inline_progress_bar": {
            "android:layout_width": "@dimen/inline_player_loading_indicator_size",
            "android:layout_height": "@dimen/inline_player_loading_indicator_size",
        },
        "inline_error_text": {
            "android:layout_margin": "@dimen/inline_player_error_margin",
            "android:padding": "@dimen/inline_player_error_padding",
            "android:textSize": "@dimen/inline_player_error_text_size_tv",
        },
        "tv_player_empty_state": {"android:padding": "@dimen/spacing_xl"},
        "tv_player_empty_title": {"android:textSize": "@dimen/text_size_tv_player_empty_title"},
        "inline_timeline_container": {
            "android:layout_height": "@dimen/inline_timeline_height_tv",
            "android:layout_marginStart": "@dimen/inline_timeline_margin_horizontal_tv",
            "android:layout_marginEnd": "@dimen/inline_timeline_margin_horizontal_tv",
            "android:layout_marginBottom": "@dimen/inline_timeline_margin_bottom_tv",
            "android:paddingStart": "@dimen/inline_timeline_padding_horizontal_tv",
            "android:paddingEnd": "@dimen/inline_timeline_padding_horizontal_tv",
        },
        "inline_time_current": {
            "android:layout_width": "@dimen/inline_timeline_time_width_tv",
            "android:textSize": "@dimen/inline_timeline_text_size_tv",
        },
        "inline_seek_bar": {"android:layout_height": "@dimen/inline_seekbar_height_tv"},
        "inline_time_duration": {
            "android:layout_width": "@dimen/inline_timeline_time_width_tv",
            "android:textSize": "@dimen/inline_timeline_text_size_tv",
        },
        "inline_controls_bar": {
            "android:paddingStart": "@dimen/inline_controls_padding_horizontal_tv",
            "android:paddingEnd": "@dimen/inline_controls_padding_horizontal_tv",
        },
        "inline_channel_logo": {
            "android:layout_width": "@dimen/inline_channel_logo_size_tv",
            "android:layout_height": "@dimen/inline_channel_logo_size_tv",
        },
        "inline_channel_name": {
            "android:layout_marginStart": "@dimen/inline_channel_name_margin_start_mobile",
            "android:textSize": "@dimen/inline_channel_name_text_size_tv",
        },
        "tv_current_channel_info": {
            "android:paddingStart": "@dimen/tv_current_channel_info_padding_horizontal",
            "android:paddingEnd": "@dimen/tv_current_channel_info_padding_horizontal",
            "android:paddingTop": "@dimen/tv_current_channel_info_padding_top",
            "android:paddingBottom": "@dimen/tv_current_channel_info_padding_bottom",
        },
        "tv_current_channel_logo": {
            "android:layout_width": "@dimen/inline_channel_logo_size_tv",
            "android:layout_height": "@dimen/inline_channel_logo_size_tv",
        },
        "tv_current_channel_name": {"android:textSize": "@dimen/text_size_channel_name_tv"},
        "tv_current_channel_category": {"android:textSize": "@dimen/text_size_caption"},
        "channels_search_container": {
            "android:layout_width": "@dimen/tv_channels_search_panel_width",
            "android:layout_marginTop": "@dimen/spacing_md",
            "android:layout_marginEnd": "@dimen/spacing_md",
            "android:paddingHorizontal": "@dimen/spacing_xs",
            "android:paddingVertical": "@dimen/spacing_xs",
            "android:elevation": "@dimen/tv_channels_search_elevation",
        },
        "btn_search": {
            "android:layout_width": "@dimen/channels_search_icon_size",
            "android:layout_height": "@dimen/channels_search_icon_size",
        },
        "search_input": {
            "android:layout_marginStart": "@dimen/search_field_margin_start",
            "android:textSize": "@dimen/text_size_body",
        },
        "tv_player_action_row": {
            "android:layout_marginTop": "@dimen/tv_player_action_row_margin_top",
            "android:paddingStart": "@dimen/tv_player_action_row_padding_horizontal",
            "android:paddingEnd": "@dimen/tv_player_action_row_padding_horizontal",
        },
        "tv_inline_channels_button": {
            "android:layout_width": "@dimen/player_control_size_tv",
            "android:layout_height": "@dimen/player_control_size_tv",
            "android:layout_marginEnd": "@dimen/tv_player_action_button_margin_end",
            "android:padding": "@dimen/tv_player_action_button_padding",
        },
        "tv_inline_search_button": {
            "android:layout_width": "@dimen/player_control_size_tv",
            "android:layout_height": "@dimen/player_control_size_tv",
            "android:padding": "@dimen/tv_player_action_button_padding",
        },
        "tv_channels_panel": {
            "android:paddingStart": "@dimen/spacing_sm",
            "android:paddingEnd": "@dimen/spacing_sm",
            "android:paddingTop": "@dimen/spacing_xs",
            "android:paddingBottom": "@dimen/spacing_sm",
        },
        "channels_section_title": {"android:textSize": "@dimen/tv_channels_section_title_text_size"},
        "channels_section_subtitle": {
            "android:layout_marginTop": "@dimen/tv_channels_subtitle_margin_top",
            "android:textSize": "@dimen/text_size_label",
        },
        "tv_channels_scroll_up": {
            "android:layout_height": "@dimen/tv_channels_scroll_hint_height",
            "android:textSize": "@dimen/text_size_caption",
        },
        "channels_recycler": {
            "android:paddingTop": "@dimen/channels_recycler_padding_top_tv",
            "android:paddingBottom": "@dimen/channels_recycler_padding_bottom_tv",
            "android:paddingStart": "@dimen/channels_recycler_padding_horizontal_tv",
            "android:paddingEnd": "@dimen/channels_recycler_padding_horizontal_tv",
        },
        "state_container": {"android:padding": "@dimen/spacing_xl"},
        "error_text": {"android:textSize": "@dimen/channels_error_text_size"},
        "retry_button": {
            "android:layout_marginTop": "@dimen/spacing_lg",
            "android:paddingHorizontal": "@dimen/spacing_xl",
            "android:paddingVertical": "@dimen/spacing_md",
            "android:textSize": "@dimen/text_size_body",
        },
        "tv_channels_scroll_down": {
            "android:layout_height": "@dimen/tv_channels_scroll_hint_height",
            "android:textSize": "@dimen/text_size_caption",
        },
        "tv_list_guide": {"android:textSize": "@dimen/text_size_label"},
    })

    mobile = L / "fragment_channels.xml"
    set_view_attributes(mobile, {
        "inline_progress_bar": {
            "android:layout_width": "@dimen/inline_player_loading_indicator_size",
            "android:layout_height": "@dimen/inline_player_loading_indicator_size",
        },
        "inline_error_text": {
            "android:layout_margin": "@dimen/inline_player_error_margin",
            "android:padding": "@dimen/inline_player_error_padding",
            "android:textSize": "@dimen/inline_player_error_text_size_mobile",
        },
        "tv_player_empty_state": {"android:padding": "@dimen/spacing_md"},
        "inline_timeline_container": {
            "android:layout_height": "@dimen/inline_timeline_height_mobile",
            "android:layout_marginStart": "@dimen/inline_timeline_margin_horizontal_mobile",
            "android:layout_marginEnd": "@dimen/inline_timeline_margin_horizontal_mobile",
            "android:layout_marginBottom": "@dimen/inline_timeline_margin_bottom_mobile",
            "android:paddingStart": "@dimen/inline_timeline_padding_horizontal_mobile",
            "android:paddingEnd": "@dimen/inline_timeline_padding_horizontal_mobile",
        },
        "inline_time_current": {
            "android:layout_width": "@dimen/inline_timeline_time_width_mobile",
            "android:textSize": "@dimen/text_size_player_time",
        },
        "inline_seek_bar": {"android:layout_height": "@dimen/inline_seekbar_height_mobile"},
        "inline_time_duration": {
            "android:layout_width": "@dimen/inline_timeline_time_width_mobile",
            "android:textSize": "@dimen/text_size_player_time",
        },
        "inline_controls_bar": {
            "android:paddingStart": "@dimen/inline_controls_padding_horizontal",
            "android:paddingEnd": "@dimen/inline_controls_padding_horizontal",
            "android:paddingTop": "@dimen/inline_controls_padding_vertical",
            "android:paddingBottom": "@dimen/inline_controls_padding_vertical",
        },
        "inline_channel_logo": {
            "android:layout_width": "@dimen/inline_channel_logo_size_mobile",
            "android:layout_height": "@dimen/inline_channel_logo_size_mobile",
        },
        "inline_channel_name": {
            "android:layout_marginStart": "@dimen/inline_channel_name_margin_start_mobile",
            "android:textSize": "@dimen/inline_channel_name_text_size_mobile",
        },
        "channels_section_header": {
            "android:paddingStart": "@dimen/channels_section_header_padding_horizontal_mobile",
            "android:paddingEnd": "@dimen/channels_section_header_padding_horizontal_mobile",
            "android:paddingTop": "@dimen/spacing_sm",
            "android:paddingBottom": "@dimen/channels_section_header_padding_bottom_mobile",
        },
        "channels_section_subtitle": {"android:layout_marginTop": "@dimen/tv_channels_subtitle_margin_top"},
        "channels_search_container": {
            "android:paddingHorizontal": "@dimen/channels_search_padding_mobile",
            "android:paddingTop": "@dimen/channels_search_padding_top_mobile",
            "android:paddingBottom": "@dimen/channels_search_padding_bottom_mobile",
        },
        "btn_search": {
            "android:layout_width": "@dimen/channels_search_icon_size",
            "android:layout_height": "@dimen/channels_search_icon_size",
        },
        "search_input": {
            "android:layout_marginStart": "@dimen/search_field_margin_start",
            "android:textSize": "@dimen/search_field_text_size_mobile",
        },
        "categories_scroll": {
            "android:paddingHorizontal": "@dimen/channels_categories_padding_horizontal_mobile",
            "android:paddingVertical": "@dimen/channels_categories_padding_vertical_mobile",
        },
        "channels_recycler": {
            "android:paddingHorizontal": "@dimen/channels_recycler_padding_horizontal_mobile",
            "android:paddingTop": "@dimen/channels_recycler_padding_top_mobile",
            "android:paddingBottom": "@dimen/channels_recycler_padding_bottom_mobile",
        },
        "state_container": {"android:padding": "@dimen/spacing_xl"},
        "error_text": {"android:textSize": "@dimen/channels_error_text_size"},
        "retry_button": {
            "android:layout_marginTop": "@dimen/spacing_lg",
            "android:paddingHorizontal": "@dimen/spacing_xl",
            "android:paddingVertical": "@dimen/spacing_md",
            "android:textSize": "@dimen/text_size_body",
        },
    })

    # Source ZIP had a stray non-XML wrapper at EOF, which prevents AAPT from parsing this layout.
    p = L / "fragment_channels_tv.xml"
    write(p, read(p).replace("\n    </document_content>", ""))

    # Empty Android backgrounds are invalid resource values. They were intended
    # to mean "no explicit background", so remove the attribute instead.
    for layout in L.glob("*.xml"):
        s = read(layout)
        s = re.sub(r'\s+android:background=""', "", s)
        write(layout, s)


def update_kotlin():
    p = J / "MainActivity.kt"
    s = read(p)
    repl = {
        'dp(72)': 'dimen(R.dimen.tv_navigation_rail_collapsed_width)',
        'dp(232)': 'dimen(R.dimen.tv_navigation_rail_expanded_width)',
        'params.width = dp(164)': 'params.width = dimen(R.dimen.header_logo_width)',
        'params.height = dp(42)': 'params.height = dimen(R.dimen.header_logo_height_tv)',
        'params.marginStart = dp(24)': 'params.marginStart = dimen(R.dimen.header_logo_margin_start_tv)',
        'buttonParams.width = dp(48)': 'buttonParams.width = dimen(R.dimen.header_search_button_size_tv)',
        'buttonParams.height = dp(48)': 'buttonParams.height = dimen(R.dimen.header_search_button_size_tv)',
        'buttonParams.marginEnd = dp(12)': 'buttonParams.marginEnd = dimen(R.dimen.header_search_button_margin_end_tv)',
        'height = dp(48)': 'height = dimen(R.dimen.header_height_mobile)',
        'contentParams.topMargin = dp(48)': 'contentParams.topMargin = dimen(R.dimen.header_height_mobile)',
        'logoParams.width = dp(164)': 'logoParams.width = dimen(R.dimen.header_logo_width)',
        'logoParams.height = dp(30)': 'logoParams.height = dimen(R.dimen.header_logo_height_mobile)',
        'logoParams.marginStart = dp(12)': 'logoParams.marginStart = dimen(R.dimen.header_logo_margin_start_mobile)',
        '    private fun dp(value: Int): Int = (value * resources.displayMetrics.density + 0.5f).toInt()\n': '    private fun dimen(resourceId: Int): Int = resources.getDimensionPixelSize(resourceId)\n',
    }
    for a, b in repl.items():
        s = s.replace(a, b)

    # La cabecera se comparte entre dispositivos, pero el reloj pertenece únicamente a TV.
    for method, statement in (
        ("    private fun setupTvHeader() {\n", "        binding.headerClock.visibility = View.VISIBLE\n"),
        ("    private fun setupMobileHeader() {\n", "        binding.headerClock.visibility = View.GONE\n"),
    ):
        start = s.find(method)
        if start < 0:
            raise SystemExit(f"Missing header setup method: {method.strip()}")
        next_method = s.find("\n    private fun ", start + len(method))
        if next_method < 0:
            next_method = len(s)
        body = s[start:next_method]
        if statement.strip() not in body:
            insert_at = start + len(method)
            s = s[:insert_at] + statement + s[insert_at:]

    write(p, s)

    p = U / "ChannelCategoryBarController.kt"
    s = read(p)
    if "import android.util.TypedValue" not in s:
        s = s.replace("import android.view.ViewGroup\n", "import android.view.ViewGroup\nimport android.util.TypedValue\n")
    for a, b in {
        "dp(TV_CHIP_HEIGHT_DP)": "dimen(R.dimen.category_chip_height_tv)",
        "chip.setPadding(dp(12), 0, dp(12), 0)": "chip.setPadding(dimen(R.dimen.category_country_chip_padding_horizontal_tv), 0, dimen(R.dimen.category_country_chip_padding_horizontal_tv), 0)",
        "chip.setPadding(dp(16), 0, dp(16), 0)": "chip.setPadding(dimen(R.dimen.category_chip_padding_horizontal_tv), 0, dimen(R.dimen.category_chip_padding_horizontal_tv), 0)",
        "chip.textSize = TV_CHIP_TEXT_SIZE_SP": "chip.setTextSize(TypedValue.COMPLEX_UNIT_PX, context.resources.getDimension(R.dimen.category_chip_text_size))",
        "dp(TV_CHIP_MARGIN_END_DP)": "dimen(R.dimen.category_chip_margin_end_tv)",
        "    private fun dp(value: Int): Int = (value * context.resources.displayMetrics.density + 0.5f).toInt()\n\n": "    private fun dimen(resourceId: Int): Int = context.resources.getDimensionPixelSize(resourceId)\n\n",
        "        const val TV_CHIP_HEIGHT_DP = 38\n        const val TV_CHIP_TEXT_SIZE_SP = 13f\n        const val TV_CHIP_MARGIN_END_DP = 8\n": "",
    }.items():
        s = s.replace(a, b)

    # Inflate responsive chip layouts from XML; Kotlin owns dynamic state and focus only.
    s = s.replace(
        ".inflate(R.layout.item_category, container, false)",
        ".inflate(if (isTV) R.layout.item_category_tv else R.layout.item_category, container, false)"
    )
    for visual_line in (
        "            chip.layoutParams = chip.layoutParams.apply { height = dimen(R.dimen.category_chip_height_tv) }\n",
        "            chip.setPadding(dimen(R.dimen.category_country_chip_padding_horizontal_tv), 0, dimen(R.dimen.category_country_chip_padding_horizontal_tv), 0)\n",
        "        chip.layoutParams = chip.layoutParams.apply { height = dimen(R.dimen.category_chip_height_tv) }\n",
        "        chip.setPadding(dimen(R.dimen.category_chip_padding_horizontal_tv), 0, dimen(R.dimen.category_chip_padding_horizontal_tv), 0)\n",
        "        chip.setTextSize(TypedValue.COMPLEX_UNIT_PX, context.resources.getDimension(R.dimen.category_chip_text_size))\n",
        "        updateChipStyle(chip, chip.isSelected)\n",
        "            updateChipStyle(chip, selected)\n",
        "            updateChipStyle(this, isFiltered)\n",
    ):
        s = s.replace(visual_line, "")
    s = s.replace("""        (chip.layoutParams as? ViewGroup.MarginLayoutParams)?.let { params ->
            params.marginEnd = dimen(R.dimen.category_chip_margin_end_tv)
            chip.layoutParams = params
        }
""", "")
    s = re.sub(
        r"    private fun updateChipStyle\(chip: TextView, isSelected: Boolean\) \{\n.*?\n    \}\n\n    private fun setupTVFocusEffect",
        "    private fun setupTVFocusEffect",
        s,
        count=1,
        flags=re.S
    )
    for unused_import in ("import android.view.ViewGroup\n", "import android.util.TypedValue\n", "import androidx.core.content.ContextCompat\n"):
        s = s.replace(unused_import, "")
    s = s.replace("    private fun dimen(resourceId: Int): Int = context.resources.getDimensionPixelSize(resourceId)\n\n", "")

    write(p, s)

    p = U / "ChannelScreenLayoutController.kt"
    s = read(p)
    if "import android.util.TypedValue" not in s:
        s = s.replace("import android.widget.TextView\n", "import android.widget.TextView\nimport android.util.TypedValue\n")
    if "import com.angulismotv.R" not in s:
        s = s.replace("import android.util.TypedValue\n", "import android.util.TypedValue\nimport com.angulismotv.R\n")
    repl = {
        'channelsSearchContainer.setPadding(dp(4), dp(4), dp(4), dp(4))':'channelsSearchContainer.setPadding(dimen(R.dimen.channels_search_padding_tv), dimen(R.dimen.channels_search_padding_tv), dimen(R.dimen.channels_search_padding_tv), dimen(R.dimen.channels_search_padding_tv))',
        'resizeSearchField(searchField, heightDp = 46, textSizeSp = 15f, marginStartDp = 8)':'resizeSearchField(searchField, heightRes = R.dimen.search_field_height_tv, textSizeRes = R.dimen.search_field_text_size_tv, marginStartRes = R.dimen.search_field_margin_start)',
        'categoriesScroll.setPadding(dp(4), dp(4), dp(4), dp(4))':'categoriesScroll.setPadding(dimen(R.dimen.channels_categories_padding_tv), dimen(R.dimen.channels_categories_padding_tv), dimen(R.dimen.channels_categories_padding_tv), dimen(R.dimen.channels_categories_padding_tv))',
        'channelsRecycler.setPadding(dp(2), dp(4), dp(2), dp(6))':'channelsRecycler.setPadding(dimen(R.dimen.channels_recycler_padding_horizontal_tv), dimen(R.dimen.channels_recycler_padding_top_tv), dimen(R.dimen.channels_recycler_padding_horizontal_tv), dimen(R.dimen.channels_recycler_padding_bottom_tv))',
        'channelsSearchContainer.setPadding(dp(8), dp(3), dp(8), dp(2))':'channelsSearchContainer.setPadding(dimen(R.dimen.channels_search_padding_mobile), dimen(R.dimen.channels_search_padding_top_mobile), dimen(R.dimen.channels_search_padding_mobile), dimen(R.dimen.channels_search_padding_bottom_mobile))',
        'resizeSearchField(searchField, heightDp = 44, textSizeSp = 14f, marginStartDp = 8)':'resizeSearchField(searchField, heightRes = R.dimen.search_field_height_mobile, textSizeRes = R.dimen.search_field_text_size_mobile, marginStartRes = R.dimen.search_field_margin_start)',
        'categoriesScroll.setPadding(dp(8), dp(2), dp(8), dp(2))':'categoriesScroll.setPadding(dimen(R.dimen.channels_categories_padding_horizontal_mobile), dimen(R.dimen.channels_categories_padding_vertical_mobile), dimen(R.dimen.channels_categories_padding_horizontal_mobile), dimen(R.dimen.channels_categories_padding_vertical_mobile))',
        'channelsRecycler.setPadding(dp(4), dp(1), dp(4), dp(8))':'channelsRecycler.setPadding(dimen(R.dimen.channels_recycler_padding_horizontal_mobile), dimen(R.dimen.channels_recycler_padding_top_mobile), dimen(R.dimen.channels_recycler_padding_horizontal_mobile), dimen(R.dimen.channels_recycler_padding_bottom_mobile))',
        'playerParams?.setMargins(dp(2), dp(2), dp(2), 0)':'playerParams?.setMargins(dimen(R.dimen.inline_player_container_margin_mobile), dimen(R.dimen.inline_player_container_margin_mobile), dimen(R.dimen.inline_player_container_margin_mobile), 0)',
        'minimumHeight = dp(44)\n            setPadding(dp(6), dp(2), dp(6), dp(2))':'minimumHeight = dimen(R.dimen.inline_controls_min_height)\n            setPadding(dimen(R.dimen.inline_controls_padding_horizontal), dimen(R.dimen.inline_controls_padding_vertical), dimen(R.dimen.inline_controls_padding_horizontal), dimen(R.dimen.inline_controls_padding_vertical))',
        'width = dp(28)\n            height = dp(28)':'width = dimen(R.dimen.inline_channel_logo_size_mobile)\n            height = dimen(R.dimen.inline_channel_logo_size_mobile)',
        'textSize = 12f':'setTextSize(TypedValue.COMPLEX_UNIT_PX, root.resources.getDimension(R.dimen.inline_channel_name_text_size_mobile))',
        'params.marginStart = dp(6)':'params.marginStart = dimen(R.dimen.inline_channel_name_margin_start_mobile)',
        'params.height = dp(24)\n            params.leftMargin = dp(8)\n            params.rightMargin = dp(8)\n            params.bottomMargin = dp(46)':'params.height = dimen(R.dimen.inline_timeline_height_mobile)\n            params.leftMargin = dimen(R.dimen.inline_timeline_margin_horizontal_mobile)\n            params.rightMargin = dimen(R.dimen.inline_timeline_margin_horizontal_mobile)\n            params.bottomMargin = dimen(R.dimen.inline_timeline_margin_bottom_mobile)',
        'width = dp(32)':'width = dimen(R.dimen.inline_timeline_time_width_mobile)',
        'inlineTimeCurrent.textSize = 9f\n        inlineTimeDuration.textSize = 9f':'inlineTimeCurrent.setTextSize(TypedValue.COMPLEX_UNIT_PX, root.resources.getDimension(R.dimen.text_size_player_time))\n        inlineTimeDuration.setTextSize(TypedValue.COMPLEX_UNIT_PX, root.resources.getDimension(R.dimen.text_size_player_time))',
        'height = dp(20)':'height = dimen(R.dimen.inline_seekbar_height_mobile)',
        'heightDp: Int,\n        textSizeSp: Float,\n        marginStartDp: Int':'heightRes: Int,\n        textSizeRes: Int,\n        marginStartRes: Int',
        'params.height = dp(heightDp)':'params.height = dimen(heightRes)',
        'searchField?.setPadding(dp(12), 0, dp(12), 0)':'searchField?.setPadding(dimen(R.dimen.search_field_padding_horizontal), 0, dimen(R.dimen.search_field_padding_horizontal), 0)',
        'searchInput.textSize = textSizeSp':'searchInput.setTextSize(TypedValue.COMPLEX_UNIT_PX, root.resources.getDimension(textSizeRes))',
        'params.marginStart = dp(marginStartDp)':'params.marginStart = dimen(marginStartRes)',
        '    private fun dp(value: Int): Int =\n        (value * root.resources.displayMetrics.density + 0.5f).toInt()':'    private fun dimen(resourceId: Int): Int = root.resources.getDimensionPixelSize(resourceId)',
    }
    for a, b in repl.items():
        s = s.replace(a, b)
    write(p, s)

    p = U / "PlayerControlsLayoutController.kt"
    s = read(p)
    if "import com.angulismotv.R" not in s:
        s = s.replace("import android.widget.LinearLayout\n", "import android.widget.LinearLayout\nimport com.angulismotv.R\n")
    for a, b in {
        'utilityParams.marginStart = dp(8)':'utilityParams.marginStart = dimen(R.dimen.player_control_spacing_compact)',
        'bottomControls.setPadding(dp(16), dp(10), dp(16), dp(12))':'bottomControls.setPadding(dimen(R.dimen.player_controls_horizontal_padding_compact), dimen(R.dimen.player_controls_padding_top), dimen(R.dimen.player_controls_horizontal_padding_compact), dimen(R.dimen.player_controls_padding_bottom))',
        'transportParams.marginStart = dp(12)':'transportParams.marginStart = dimen(R.dimen.player_control_spacing_regular)',
        'utilityParams.marginStart = dp(12)':'utilityParams.marginStart = dimen(R.dimen.player_control_spacing_regular)',
        'bottomControls.setPadding(dp(22), dp(10), dp(22), dp(12))':'bottomControls.setPadding(dimen(R.dimen.player_controls_horizontal_padding_wide), dimen(R.dimen.player_controls_padding_top), dimen(R.dimen.player_controls_horizontal_padding_wide), dimen(R.dimen.player_controls_padding_bottom))',
        '    private fun dp(value: Int): Int =\n        (value * context.resources.displayMetrics.density + 0.5f).toInt()':'    private fun dimen(resourceId: Int): Int = context.resources.getDimensionPixelSize(resourceId)',
    }.items():
        s = s.replace(a, b)
    write(p, s)

    p = J / "UnifiedPlayerActivity.kt"
    s = read(p)
    center_transport_arg = "            centerTransportControlsContainer = findViewById(R.id.center_transport_controls_container)"
    if center_transport_arg not in s:
        bottom_controls_marker = "            bottomControls = bottomControls\n"
        if bottom_controls_marker not in s:
            raise SystemExit("Missing bottomControls constructor argument in UnifiedPlayerActivity")
        s = s.replace(bottom_controls_marker, "            bottomControls = bottomControls,\n" + center_transport_arg + "\n", 1)
    s=s.replace('    private fun dp(value: Int): Int = (value * resources.displayMetrics.density + 0.5f).toInt()\n\n','')
    s=s.replace('val size = (48 * resources.displayMetrics.density + 0.5f).toInt()','val size = resources.getDimensionPixelSize(R.dimen.player_control_size_tv)')
    s=s.replace('val maxNameWidthDp = if (isTV) 480 else 220\n            maxWidth = (maxNameWidthDp * resources.displayMetrics.density).toInt()','val maxNameWidthRes = if (isTV) R.dimen.zapping_label_max_width_tv else R.dimen.zapping_label_max_width_mobile\n            maxWidth = resources.getDimensionPixelSize(maxNameWidthRes)')

    # El estado visual por tipo de reproducción se separa de la Activity.
    if "import com.angulismotv.ui.PlayerControlStateController" not in s:
        s = s.replace(
            "import com.angulismotv.ui.PlayerControlsLayoutController\n",
            "import com.angulismotv.ui.PlayerControlsLayoutController\nimport com.angulismotv.ui.PlayerControlStateController\n"
        )
    field_marker = "    private lateinit var timelineController: PlayerTimelineController\n"
    if "private lateinit var playerControlStateController: PlayerControlStateController" not in s:
        if field_marker not in s:
            raise SystemExit("Missing timelineController field in UnifiedPlayerActivity")
        s = s.replace(
            field_marker,
            field_marker + "    private lateinit var playerControlStateController: PlayerControlStateController\n"
        )

    setup_marker = "        playerControlsLayoutController.apply(resources.configuration.orientation)\n"
    if "playerControlStateController = PlayerControlStateController(" not in s:
        if setup_marker not in s:
            raise SystemExit("Missing PlayerControlsLayoutController setup marker")
        setup_block = """        playerControlStateController = PlayerControlStateController(
            isTv = { isTV },
            streamType = { currentStreamType },
            castConfigured = { cast.isConfigured },
            hasMultipleOptions = ::hasMultipleOptions,
            currentIsLive = { currentIsLive },
            streamIsLive = { streamIsLive },
            iframeIsControllable = { webBridge.isControllable },
            iframeIsPlaying = { webBridge.isPlaying },
            iframeDurationMs = { webBridge.duration },
            menuButton = btnMenu,
            playPauseButton = btnPlayPause,
            rewindButton = btnRewind,
            forwardButton = btnForward,
            optionsButton = btnOptions,
            reloadButton = btnReloadStream,
            closeButton = btnClose,
            castButton = mediaRouteButton,
            onPlayStateChanged = ::updatePlayPauseButton,
            updateControlFocusOrder = ::updateControlFocusOrder
        )
"""
        s = s.replace(setup_marker, setup_block + setup_marker)

    delegated_method = "    private fun updateControlsVisibility() = playerControlStateController.updateControlsVisibility()"
    if delegated_method not in s:
        state_pattern = re.compile(
            r'    private fun updateControlsVisibility\(\) \{.*?(?=    private fun updateFavoriteButton\()',
            re.S
        )
        match = state_pattern.search(s)
        if not match:
            raise SystemExit("Missing player controls state methods for extraction")
        replacement = """    private fun updateControlsVisibility() = playerControlStateController.updateControlsVisibility()

    private fun updateCastButtonVisibility() = playerControlStateController.updateCastButtonVisibility()

    private fun updateTransportControlsVisibility() = playerControlStateController.updateTransportControlsVisibility()

    private fun updateIframeTransportControls() = playerControlStateController.updateIframeTransportControls()

    private fun updateNativeTransportControls() = playerControlStateController.updateNativeTransportControls()

    private fun configureTvControlFocusOrder() = playerControlStateController.configureTvControlFocusOrder()

"""
        s = s[:match.start()] + replacement + s[match.end():]

    write(p,s)


def design_doc():
    write(ROOT / "SISTEMA-DISENO-UI.md", """# Sistema de diseño visual de AngulismoTV

## Dónde personalizar
- app/src/main/res/values/colors.xml: paleta Aqua espacial, superficies, contraste y estados.
- app/src/main/res/values/dimens.xml: escalas de espaciado/tipografía y tamaños adaptados a móvil y Android TV.
- app/src/main/res/values/styles.xml: estilos comunes de textos, chips y controles del reproductor.
- app/src/main/res/layout/item_channel.xml e item_channel_tv.xml: filas de canales en XML para móvil y TV.
- app/src/main/res/layout/item_category.xml e item_category_tv.xml: medidas de chips en XML.
- Selectores de estado en res/drawable y res/color: colores de selección de categorías definidos en XML.
- app/src/main/res/drawable/: fondos, bordes, selectores de foco y estados de interacción.
- app/src/main/res/layout/: estructura de las pantallas; mantener referencias a tokens compartidos.

## Componentes conectados
Botones de acción y transporte del reproductor, acción primaria, carga/error, zapping, cronología, identidad del canal, controles inline, búsqueda de cabecera, chips, nombre/número de canal, conteos y reloj. Las decisiones de visibilidad y foco por modo de reproducción están en PlayerControlStateController; las medidas fijas se centralizan en dimens.xml y Kotlin conserva la orquestación de sesión.

## Reglas
1. Ajustar primero un token común; crear una excepción por pantalla solo cuando sea necesaria.
2. Mantener separado layout (estructura), styles (apariencia), drawables (fondos/estados) y Kotlin (comportamiento).
3. En Android TV, el foco visible y la navegación D-pad son obligatorios.
4. Mostrar el reloj de la cabecera únicamente en Android TV; mantenerlo oculto en móvil.
5. Conservar la reproducción, favoritos, recarga, pantalla completa, Cast, selección de fuente, orientación y navegación existentes.
6. Mantener el vídeo en negro real; evitar blur, partículas y animaciones permanentes para no elevar el coste gráfico.

Esta es una primera etapa incremental: prioriza los componentes repetidos y los valores más propensos a cambios globales. La extracción adicional de lógica de ChannelsFragment y UnifiedPlayerActivity debe hacerse separando responsabilidades con pruebas, no con una sustitución masiva.
""")



def fix_tv_channel_number_initialization():
    """Prepare TV channel numbers before the first list render."""
    p = J / "fragments" / "ChannelsFragment.kt"
    s = read(p)
    old = """        if (isTV) {
            applyFiltersAndUpdate { restoreLastActiveChannel(channels) }
            return
        }
"""
    new = """        if (isTV) {
            categoryMetadataJob?.cancel()
            val expectedViewGeneration = viewGeneration
            categoryMetadataJob = viewLifecycleOwner.lifecycleScope.launch {
                val channelNumbers = withContext(Dispatchers.Default) {
                    ChannelCatalog.channelNumbersByIdentity(channels)
                }
                if (expectedViewGeneration != viewGeneration || view == null || !isAdded ||
                    originalChannels !== channels) return@launch

                // Los números deben estar disponibles antes del primer render en TV.
                // De lo contrario, el adaptador muestra "—" para todos los canales.
                channelNumbersByIdentity = channelNumbers
                applyFiltersAndUpdate { restoreLastActiveChannel(channels) }
            }
            return
        }
"""
    if old not in s:
        if new in s:
            return
        raise SystemExit("No se encontró la rama TV esperada en generateCategoriesFromChannels")
    write(p, s.replace(old, new, 1))

def main():
    if not (ROOT / "settings.gradle.kts").exists():
        raise SystemExit(f"Not a Gradle Android root: {ROOT}")
    token_dimensions()
    component_styles()
    update_xml()
    update_kotlin()
    fix_tv_channel_number_initialization()
    design_doc()
    print("UI design system applied")


if __name__ == "__main__":
    main()
