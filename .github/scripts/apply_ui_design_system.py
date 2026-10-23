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
    for view in ("btn_menu", "btn_options", "btn_favorite_channel", "btn_reload_stream", "btn_close_player"):
        style_view(p, view, "style", "Widget.AngulismoTV.PlayerActionButton", ("android:background", "android:padding"))
    for view in ("btn_rewind", "btn_forward"):
        style_view(p, view, "style", "Widget.AngulismoTV.PlayerTransportButton", ("android:background", "android:padding"))
    style_view(p, "btn_play_pause", "style", "Widget.AngulismoTV.PlayerPrimaryButton", ("android:background", "android:padding"))
    s = read(p).replace('android:layout_width="48dp" android:layout_height="48dp"', 'android:layout_width="@dimen/player_primary_action_size" android:layout_height="@dimen/player_primary_action_size"')
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
    s=s.replace('    private fun dp(value: Int): Int = (value * resources.displayMetrics.density + 0.5f).toInt()\n\n','')
    s=s.replace('val size = (48 * resources.displayMetrics.density + 0.5f).toInt()','val size = resources.getDimensionPixelSize(R.dimen.player_control_size_tv)')
    s=s.replace('val maxNameWidthDp = if (isTV) 480 else 220\n            maxWidth = (maxNameWidthDp * resources.displayMetrics.density).toInt()','val maxNameWidthRes = if (isTV) R.dimen.zapping_label_max_width_tv else R.dimen.zapping_label_max_width_mobile\n            maxWidth = resources.getDimensionPixelSize(maxNameWidthRes)')
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
Botones de acción y transporte del reproductor, acción primaria, controles inline, búsqueda de cabecera, chips, nombre/número de canal, conteos y reloj. Los controladores de cabecera, categorías, reproductor integrado y fila de controles fullscreen leen los valores de dimens.xml.

## Reglas
1. Ajustar primero un token común; crear una excepción por pantalla solo cuando sea necesaria.
2. Mantener separado layout (estructura), styles (apariencia), drawables (fondos/estados) y Kotlin (comportamiento).
3. En Android TV, el foco visible y la navegación D-pad son obligatorios.
4. Conservar la reproducción, favoritos, recarga, pantalla completa, Cast, selección de fuente, orientación y navegación existentes.
5. Mantener el vídeo en negro real; evitar blur, partículas y animaciones permanentes para no elevar el coste gráfico.

Esta es una primera etapa incremental: prioriza los componentes repetidos y los valores más propensos a cambios globales. La extracción adicional de lógica de ChannelsFragment y UnifiedPlayerActivity debe hacerse separando responsabilidades con pruebas, no con una sustitución masiva.
""")


def main():
    if not (ROOT / "settings.gradle.kts").exists():
        raise SystemExit(f"Not a Gradle Android root: {ROOT}")
    token_dimensions()
    component_styles()
    update_xml()
    update_kotlin()
    design_doc()
    print("UI design system applied")


if __name__ == "__main__":
    main()
