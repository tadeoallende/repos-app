#!/usr/bin/env python3
"""Apply tracked source overlays to the Android project ZIP before GitHub Actions builds it."""
from __future__ import annotations
import os
import re
from pathlib import Path
import sys
import tempfile
import zipfile



def replace_once(text: str, old: str, new: str, label: str) -> str:
    # First check the full replacement because many imports/headers are prefixes of themselves.
    if new in text:
        return text
    if old in text:
        return text.replace(old, new)
    raise RuntimeError(f"No se pudo aplicar {label}: el código base no coincide.")



def apply_nebula_visuals(name: str, text: str) -> str:
    """Apply the midnight/nebula palette and polish channel rows without changing their data."""
    if not name.endswith(".xml") or "/res/" not in name:
        return text

    import xml.etree.ElementTree as ET
    android_ns = "{http://schemas.android.com/apk/res/android}"
    ET.register_namespace("android", android_ns[1:-1])
    ET.register_namespace("app", "http://schemas.android.com/apk/res-auto")
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return text

    if "/res/values" in name and Path(name).name == "colors.xml":
        for node in root.iter():
            tag = node.tag.split("}")[-1]
            if tag == "color":
                resource_name = (node.get("name") or "").lower().replace("-", "_")
            elif tag == "item" and node.get("type") == "color":
                resource_name = (node.get("name") or "").lower().replace("-", "_")
            else:
                continue

            value = None
            if any(token in resource_name for token in ("text_primary", "primary_text", "text_main")):
                value = "#EDF2FA"
            elif any(token in resource_name for token in ("text_secondary", "secondary_text", "text_subtitle")):
                value = "#AAB7CA"
            elif any(token in resource_name for token in ("text_hint", "hint_text", "text_disabled")):
                value = "#8290AE"
            elif any(token in resource_name for token in ("accent", "bottom_nav_color", "brand_cyan", "color_accent")):
                value = "#5CC7C6"
            elif any(token in resource_name for token in ("divider", "outline", "stroke", "border")):
                value = "#26324A"
            elif any(token in resource_name for token in ("nebula", "cosmic", "space_purple", "indigo_accent")):
                value = "#8D7CFF"
            elif resource_name in ("colorprimarydark", "color_primary_dark", "background", "app_background", "window_background", "screen_background", "bg_primary", "colorbackground", "color_background", "background_dark", "background_primary", "bg_app", "bg_screen") or any(token in resource_name for token in ("app_background", "window_background", "screen_background", "background_dark", "background_primary", "bg_primary", "bg_app", "bg_screen")):
                value = "#080D1B"
            elif any(token in resource_name for token in ("surface", "card", "panel", "background_surface", "surface_background")):
                value = "#11182A"
            elif resource_name in ("colorprimary", "color_primary", "primary_accent"):
                value = "#63E6E0"

            if value:
                node.text = value
        return ET.tostring(root, encoding="unicode", xml_declaration=True)

    if "/res/layout/" not in name:
        return text

    layout_name = Path(name).stem.lower()
    # The TV panel is handled separately; this transform only targets reusable channel rows.
    excluded = ("fragment_", "activity_", "dialog_", "bottom_sheet", "player", "panel", "header")
    has_channel_hint = "channel" in layout_name or "canal" in layout_name
    if not has_channel_hint or any(token in layout_name for token in excluded):
        return text

    view_nodes = list(root.iter())
    image_nodes = [node for node in view_nodes if node.tag.split("}")[-1] in
                   ("ImageView", "AppCompatImageView", "ShapeableImageView")]
    text_nodes = [node for node in view_nodes if node.tag.split("}")[-1] in
                  ("TextView", "AppCompatTextView", "MaterialTextView")]
    if not image_nodes or not text_nodes or root.tag.split("}")[-1] == "merge":
        return text

    # Keep XML as the source of truth. These defaults only fill gaps in older layouts.
    def set_if_missing(node, attribute, value):
        if node.get(attribute) is None:
            node.set(attribute, value)

    for attribute, value in (
        (android_ns + "background", "@drawable/bg_channel_row_nebula"),
        (android_ns + "focusable", "true"),
        (android_ns + "clickable", "true"),
        (android_ns + "paddingStart", "8dp"),
        (android_ns + "paddingEnd", "8dp"),
        (android_ns + "paddingTop", "4dp"),
        (android_ns + "paddingBottom", "4dp"),
        (android_ns + "minHeight", "52dp"),
        (android_ns + "layout_marginBottom", "2dp"),
    ):
        set_if_missing(root, attribute, value)
    if root.get(android_ns + "layout_height") in (None, "match_parent"):
        root.set(android_ns + "layout_height", "wrap_content")

    def view_id(node):
        return (node.get(android_ns + "id", "").split("/")[-1]).lower().replace("_", "")

    logo = next((node for node in image_nodes
                 if any(token in view_id(node) for token in ("logo", "channellogo", "channelimage"))), None)
    if logo is None:
        logo = next((node for node in image_nodes
                     if not any(token in view_id(node) for token in ("play", "arrow", "search", "favorite", "fav"))),
                    image_nodes[0])
    set_if_missing(logo, android_ns + "layout_width", "40dp")
    set_if_missing(logo, android_ns + "layout_height", "40dp")
    set_if_missing(logo, android_ns + "scaleType", "fitCenter")
    set_if_missing(logo, android_ns + "adjustViewBounds", "true")
    set_if_missing(logo, android_ns + "padding", "4dp")
    set_if_missing(logo, android_ns + "background", "@drawable/bg_channel_logo_container")

    primary_text = next((node for node in text_nodes
                         if any(token in view_id(node) for token in ("name", "title", "channelname", "canal"))),
                        text_nodes[0])
    for node in text_nodes:
        if node is primary_text:
            set_if_missing(node, android_ns + "textColor", "#EDF2FA")
            set_if_missing(node, android_ns + "textSize", "15sp")
            set_if_missing(node, android_ns + "fontFamily", "sans-serif-medium")
            set_if_missing(node, android_ns + "maxLines", "1")
            set_if_missing(node, android_ns + "ellipsize", "end")
        else:
            set_if_missing(node, android_ns + "textColor", "#AAB7CA")
            set_if_missing(node, android_ns + "maxLines", "1")
            set_if_missing(node, android_ns + "ellipsize", "end")

    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def apply_source_optimizations(name: str, raw: bytes) -> bytes:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw

    if name == "app/src/main/java/com/angulismotv/fragments/ChannelsFragment.kt":
        for old, new, label in [
            ("import androidx.fragment.app.Fragment\n", "import androidx.fragment.app.Fragment\nimport androidx.lifecycle.lifecycleScope\n", "imports lifecycleScope"),
            ("import com.angulismotv.ui.DebouncedChannelSearchController\n", "import com.angulismotv.ui.DebouncedChannelSearchController\nimport kotlinx.coroutines.Dispatchers\nimport kotlinx.coroutines.Job\nimport kotlinx.coroutines.launch\nimport kotlinx.coroutines.withContext\n", "imports coroutines"),
            ("    private var channelSearchController: DebouncedChannelSearchController? = null\n", "    private var channelSearchController: DebouncedChannelSearchController? = null\n    private var filterJob: Job? = null\n    private var filterGeneration = 0\n    private var categoryMetadataJob: Job? = null\n", "jobs de filtrado"),
            ("        inlinePlayerContainer.visibility = View.GONE\n        inlinePlayerView.isFocusable = false\n", "        // Mantener el marco 16:9 desde el primer render evita saltos al elegir el primer canal.\n        inlinePlayerContainer.visibility = View.VISIBLE\n        tvPlayerEmptyState?.visibility = View.VISIBLE\n        inlinePlayerView.isFocusable = false\n", "mini reproductor fijo"),
            ("if (isTV && ::channelsAdapter.isInitialized) channelsAdapter.setPreviewChannel(channel)", "if (::channelsAdapter.isInitialized) channelsAdapter.setPreviewChannel(channel)", "selección en móvil"),
            ("        inlinePlayerContainer.visibility = if (isTV) View.VISIBLE else View.GONE\n        inlineProgressBar.visibility = View.GONE\n", "        inlinePlayerContainer.visibility = View.VISIBLE\n        tvPlayerEmptyState?.visibility = View.VISIBLE\n        inlineProgressBar.visibility = View.GONE\n", "mantener marco al cerrar"),
            ("if (isTV && ::channelsAdapter.isInitialized) channelsAdapter.setPreviewChannel(null)", "if (::channelsAdapter.isInitialized) channelsAdapter.setPreviewChannel(null)", "quitar selección"),
        ]:
            text = replace_once(text, old, new, label)

        old_filter = '''    private fun applyFiltersAndUpdate(onListCommitted: (() -> Unit)? = null) {
        if (originalChannels.isEmpty()) {
            onListCommitted?.invoke()
            return
        }

        filteredChannels = ChannelFilterEngine.filter(
            channels = originalChannels,
            category = currentCategory,
            country = currentCountry,
            query = if (isSearchVisible && _searchInputRef.isInitialized &&
                searchInput.visibility == View.VISIBLE) searchInput.text.toString() else ""
        )

        val expectedViewGeneration = viewGeneration
        channelsAdapter.submitList(filteredChannels) {
            if (view != null && expectedViewGeneration == viewGeneration) onListCommitted?.invoke()
        }
        if (isTV) {
            channelsSectionSubtitle.text = if (filteredChannels.isEmpty()) {
                getString(R.string.tv_channels_subtitle_empty)
            } else {
                getString(R.string.tv_channels_subtitle_count, filteredChannels.size)
            }
        }

        if (filteredChannels.isEmpty()) {
            showState("No se encontraron canales", isError = false, showRetry = false)
        } else {
            hideState()
        }
    }
'''
        new_filter = '''    private fun applyFiltersAndUpdate(onListCommitted: (() -> Unit)? = null) {
        if (originalChannels.isEmpty()) {
            filterGeneration++
            filterJob?.cancel()
            filterJob = null
            onListCommitted?.invoke()
            return
        }

        val requestGeneration = ++filterGeneration
        val expectedViewGeneration = viewGeneration
        val sourceSnapshot = originalChannels
        val categorySnapshot = currentCategory
        val countrySnapshot = currentCountry
        val querySnapshot = if (isSearchVisible && _searchInputRef.isInitialized &&
            searchInput.visibility == View.VISIBLE) searchInput.text.toString() else ""

        filterJob?.cancel()
        filterJob = viewLifecycleOwner.lifecycleScope.launch {
            // Un catálogo grande no debe filtrar ni normalizar nombres en el hilo visual.
            val result = withContext(Dispatchers.Default) {
                ChannelFilterEngine.filter(sourceSnapshot, categorySnapshot, countrySnapshot, querySnapshot)
            }
            if (requestGeneration != filterGeneration || expectedViewGeneration != viewGeneration ||
                view == null || !isAdded || !::channelsAdapter.isInitialized) return@launch

            filteredChannels = result
            channelsAdapter.submitList(result) {
                if (requestGeneration == filterGeneration && view != null &&
                    expectedViewGeneration == viewGeneration) onListCommitted?.invoke()
            }
            if (isTV) {
                channelsSectionSubtitle.text = if (result.isEmpty()) {
                    getString(R.string.tv_channels_subtitle_empty)
                } else {
                    getString(R.string.tv_channels_subtitle_count, result.size)
                }
            }
            if (result.isEmpty()) showState("No se encontraron canales", isError = false, showRetry = false)
            else hideState()
        }
    }
'''
        text = replace_once(text, old_filter, new_filter, "filtro asíncrono")

        old_categories = '''    private fun generateCategoriesFromChannels(channels: List<Channel>) {
        if (channels.isEmpty()) return
        val availableCountries = ChannelFilterEngine.availableCountries(channels).toSet()
        if (availableCountries.isEmpty()) currentCountry = ChannelFilterEngine.ALL_COUNTRIES
        else if (currentCountry != ChannelFilterEngine.ALL_COUNTRIES && currentCountry !in availableCountries) {
            currentCountry = ChannelFilterEngine.ALL_COUNTRIES
        }
        categoryBarController?.render()
    }
'''
        new_categories = '''    private fun generateCategoriesFromChannels(channels: List<Channel>) {
        if (channels.isEmpty()) return
        categoryMetadataJob?.cancel()
        val expectedViewGeneration = viewGeneration
        categoryMetadataJob = viewLifecycleOwner.lifecycleScope.launch {
            val metadata = withContext(Dispatchers.Default) {
                ChannelFilterEngine.availableCategories(channels) to ChannelFilterEngine.availableCountries(channels)
            }
            if (expectedViewGeneration != viewGeneration || view == null || !isAdded || originalChannels !== channels) {
                return@launch
            }
            val availableCountries = metadata.second.toSet()
            if (availableCountries.isEmpty()) currentCountry = ChannelFilterEngine.ALL_COUNTRIES
            else if (currentCountry != ChannelFilterEngine.ALL_COUNTRIES && currentCountry !in availableCountries) {
                currentCountry = ChannelFilterEngine.ALL_COUNTRIES
            }
            categoryBarController?.render(metadata.first, metadata.second)
        }
    }
'''
        if old_categories in text:
            text = replace_once(text, old_categories, new_categories, "metadatos de categorías asíncronos")
        elif "categoryMetadataJob = viewLifecycleOwner.lifecycleScope.launch" not in text:
            raise RuntimeError("No se pudo aplicar metadatos de categorías asíncronos: el código base no coincide.")
        text = replace_once(text, "    private fun applyResult(result: LoadResult) {\n", "    private fun applyResult(result: LoadResult) {\n        filterGeneration++\n        filterJob?.cancel()\n        filterJob = null\n        categoryMetadataJob?.cancel()\n        categoryMetadataJob = null\n", "cancelar filtrado obsoleto")
        text = replace_once(text, "    private fun disposeViewControllers() {\n", "    private fun disposeViewControllers() {\n        filterGeneration++\n        filterJob?.cancel()\n        filterJob = null\n        categoryMetadataJob?.cancel()\n        categoryMetadataJob = null\n", "liberar trabajos del fragmento")
        text = replace_once(text,
            """            val metadata = withContext(Dispatchers.Default) {
                ChannelFilterEngine.availableCategories(channels) to ChannelFilterEngine.availableCountries(channels)
            }""",
            """            val metadata = withContext(Dispatchers.Default) {
                Triple(
                    ChannelFilterEngine.availableCategories(channels),
                    ChannelFilterEngine.availableCountries(channels),
                    ChannelCatalog.channelNumbersByIdentity(channels)
                )
            }""", "preparar índice del catálogo fuera del hilo visual")
        text = replace_once(text,
            "            val availableCountries = metadata.second.toSet()",
            "            channelNumbersByIdentity = metadata.third\n            val availableCountries = metadata.second.toSet()",
            "asignar índice preparado")
        text = replace_once(text,
            "            categoryBarController?.render(metadata.first, metadata.second)\n",
            "            categoryBarController?.render(metadata.first, metadata.second)\n            applyFiltersAndUpdate()\n",
            "filtrar al terminar la preparación")
        text = replace_once(text,
            "        originalChannels = result.channels\n        channelNumbersByIdentity = ChannelCatalog.channelNumbersByIdentity(originalChannels)\n        currentCategory = \"todos\"\n",
            "        originalChannels = result.channels\n        channelNumbersByIdentity = emptyMap()\n        currentCategory = \"todos\"\n",
            "evitar construir el índice en el hilo visual")
        text = replace_once(text,
            """        } else {
            generateCategoriesFromChannels(originalChannels)
            applyFiltersAndUpdate()
        }
    }

    private fun showState""",
            """        } else {
            generateCategoriesFromChannels(originalChannels)
        }
    }

    private fun showState""", "esperar la preparación asíncrona del catálogo")

        text = replace_once(text,
            "    private fun generateCategoriesFromChannels(channels: List<Channel>) {\n        if (channels.isEmpty()) return\n",
            "    private fun generateCategoriesFromChannels(channels: List<Channel>) {\n        if (channels.isEmpty()) return\n        if (isTV) {\n            applyFiltersAndUpdate { restoreLastActiveChannel(channels) }\n            return\n        }\n",
            "mostrar todos los canales en la pantalla principal de TV")

        if "openPlayerPanelShortcut(openSearch = true)" not in text:
            text = replace_once(text,
                """        ).also { it.attach() }
    }

    /** Opens/closes the search field from the shared header (mobile and Android TV). */""",
                """        ).also { it.attach() }
        if (isTV) {
            view?.findViewById<View>(R.id.tv_inline_search_button)?.setOnClickListener {
                toggleSearchFromHeader()
            }
        }
    }

    /** Opens/closes the search field from the shared header (mobile and Android TV). */""",
                "conectar el buscador integrado en el reproductor")

        text = replace_once(text,
            """            val opening = !isSearchVisible
            toggleSearch()
            if (opening) {
                searchInput.requestFocus()
            } else {
                activity?.findViewById<View>(R.id.header_search_button)?.requestFocus()
            }""",
            """            val opening = !isSearchVisible
            toggleSearch()
            view?.findViewById<View>(R.id.tv_inline_search_button)?.visibility =
                if (opening) View.GONE else View.VISIBLE
            if (::channelsAdapter.isInitialized) {
                channelsAdapter.setCategoryFocusTarget(
                    if (opening) R.id.search_input else R.id.tv_inline_search_button
                )
            }
            if (opening) {
                searchInput.requestFocus()
            } else {
                val playerSearchButton = view?.findViewById<View>(R.id.tv_inline_search_button)
                if (playerSearchButton?.requestFocus() != true) {
                    activity?.findViewById<View>(R.id.header_search_button)?.requestFocus()
                }
            }""",
            "mantener búsqueda y foco dentro del reproductor")

        text = replace_once(text,
            """        toggleSearch()
        activity?.findViewById<View>(R.id.header_search_button)?.requestFocus()
        return true""",
            """        toggleSearch()
        view?.findViewById<View>(R.id.tv_inline_search_button)?.visibility = View.VISIBLE
        if (::channelsAdapter.isInitialized) channelsAdapter.setCategoryFocusTarget(R.id.tv_inline_search_button)
        view?.findViewById<View>(R.id.tv_inline_search_button)?.requestFocus()
        return true""",
            "devolver el foco al buscador del reproductor al cerrar búsqueda")

        text = replace_once(text,
            "    private fun showInlinePlayer(channel: Channel, startPlayback: Boolean = true) {\n",
            """    private fun rememberLastActiveChannel(channel: Channel) {
        if (!isTV || !isAdded) return
        requireContext().getSharedPreferences("angulismotv_playback", android.content.Context.MODE_PRIVATE)
            .edit()
            .putString("last_channel_key", ChannelIdentity.key(channel))
            .putString("last_channel_name", channel.name)
            .putString("last_channel_logo", channel.logo)
            .apply()
    }

    private fun restoreLastActiveChannel(channels: List<Channel>) {
        if (!isTV || inlineChannel != null || !isAdded || channels.isEmpty()) return
        val preferences = requireContext().getSharedPreferences(
            "angulismotv_playback",
            android.content.Context.MODE_PRIVATE
        )
        val savedKey = preferences.getString("last_channel_key", null)
        val savedName = preferences.getString("last_channel_name", null).orEmpty()
        val savedLogo = preferences.getString("last_channel_logo", null)
        val lastChannel = channels.firstOrNull {
            !savedKey.isNullOrBlank() && ChannelIdentity.key(it) == savedKey
        } ?: channels.firstOrNull {
            savedName.isNotBlank() && it.name.equals(savedName, ignoreCase = true) &&
                (savedLogo.isNullOrBlank() || it.logo == savedLogo)
        } ?: channels.firstOrNull {
            savedName.isNotBlank() && it.name.equals(savedName, ignoreCase = true)
        } ?: return
        showInlinePlayer(lastChannel)
    }

    private fun showInlinePlayer(channel: Channel, startPlayback: Boolean = true) {""",
            "recordar y recuperar el último canal activo")

        text = replace_once(text,
            "        inlineChannel = channel\n        inlineSourceIndex = 0\n",
            "        inlineChannel = channel\n        rememberLastActiveChannel(channel)\n        inlineSourceIndex = 0\n",
            "guardar el último canal al seleccionarlo")

        # El ZIP queda persistido tras compilar. Permitir volver a ejecutar este parche
        # aunque el código de cierre ya esté presente con una variante de selección normalizada.
        if '        inlineChannel = null\n        if (isTV) {\n            requireContext().getSharedPreferences("angulismotv_playback", android.content.Context.MODE_PRIVATE)\n                .edit().clear().apply()' not in text:
            text = replace_once(text,
                "        inlineChannel = null\n        if (::channelsAdapter.isInitialized) channelsAdapter.setPreviewChannel(null)\n",
                """        inlineChannel = null
        if (isTV) {
            requireContext().getSharedPreferences("angulismotv_playback", android.content.Context.MODE_PRIVATE)
                .edit().clear().apply()
            view?.findViewById<View>(R.id.tv_inline_search_button)?.visibility = View.VISIBLE
            if (::channelsAdapter.isInitialized) channelsAdapter.setCategoryFocusTarget(R.id.tv_inline_search_button)
        }
        if (::channelsAdapter.isInitialized) channelsAdapter.setPreviewChannel(null)
""",
                "limpiar el último canal al cerrar expresamente el reproductor")

        text = replace_once(text,
            "        channelsSectionHeader.visibility = if (isTV) View.VISIBLE else View.GONE\n",
            "        channelsSectionHeader.visibility = View.GONE\n",
            "mantener oculta la cabecera de TV")

        text = replace_once(text,
            "            channelsRecycler.nextFocusLeftId = R.id.inline_player_container\n",
            "            channelsRecycler.nextFocusLeftId = R.id.inline_player_container\n            channelsAdapter.setCategoryFocusTarget(R.id.tv_inline_search_button)\n",
            "asignar el botón de búsqueda como destino de foco")
    elif name == "app/src/main/java/com/angulismotv/adapters/ChannelsAdapter.kt":
        text = replace_once(text, "if (isTV && itemCount > 0) notifyItemRangeChanged(0, itemCount, PAYLOAD_PREVIEW_STATE)", "if (itemCount > 0) notifyItemRangeChanged(0, itemCount, PAYLOAD_PREVIEW_STATE)", "notificar selección móvil")
        text = replace_once(text, "holder.itemView.isSelected = isTV && previewChannelKey == ChannelIdentity.key(channel)", "holder.itemView.isSelected = previewChannelKey == ChannelIdentity.key(channel)", "selección visual móvil")
        text = replace_once(text, "holder.itemView.isSelected = isTV && channel != null &&\n                previewChannelKey == ChannelIdentity.key(channel)", "holder.itemView.isSelected = channel != null && previewChannelKey == ChannelIdentity.key(channel)", "selección por payload")

        text = replace_once(text,
            """        if (isTV) {
            // La lista es la columna más a la derecha. Consumir → evita que Android busque
            // una vista no relacionada cuando no existe otra columna a la derecha.
            holder.itemView.setOnKeyListener { _, keyCode, event ->
                event.action == android.view.KeyEvent.ACTION_DOWN &&
                    keyCode == android.view.KeyEvent.KEYCODE_DPAD_RIGHT
            }
        } else {
            holder.itemView.setOnKeyListener(null)
        }""",
            """        if (isTV) {
            holder.itemView.setOnKeyListener { focusedRow, keyCode, event ->
                if (event.action != android.view.KeyEvent.ACTION_DOWN) {
                    false
                } else when (keyCode) {
                    android.view.KeyEvent.KEYCODE_DPAD_RIGHT -> true
                    android.view.KeyEvent.KEYCODE_DPAD_UP,
                    android.view.KeyEvent.KEYCODE_DPAD_DOWN -> {
                        val currentPosition = holder.bindingAdapterPosition
                        val count = differ.currentList.size
                        if (currentPosition == RecyclerView.NO_POSITION || count == 0) {
                            true
                        } else {
                            val delta = if (keyCode == android.view.KeyEvent.KEYCODE_DPAD_DOWN) 1 else -1
                            val targetPosition = currentPosition + delta
                            if (targetPosition < 0) {
                                false
                            } else if (targetPosition >= count) {
                                true
                            } else {
                                val recycler = focusedRow.parent as? RecyclerView
                                if (recycler != null) {
                                    val target = recycler.findViewHolderForAdapterPosition(targetPosition)?.itemView
                                    val fullyVisible = target != null &&
                                        target.top >= recycler.paddingTop &&
                                        target.bottom <= recycler.height - recycler.paddingBottom
                                    if (fullyVisible) {
                                        target?.requestFocus()
                                    } else {
                                        val layoutManager = recycler.layoutManager as?
                                            androidx.recyclerview.widget.LinearLayoutManager
                                        val rowHeight = focusedRow.height.takeIf { it > 0 } ?: 1
                                        val offset = if (delta > 0) {
                                            (recycler.height - recycler.paddingBottom - rowHeight)
                                                .coerceAtLeast(recycler.paddingTop)
                                        } else recycler.paddingTop
                                        layoutManager?.scrollToPositionWithOffset(targetPosition, offset)
                                        recycler.post {
                                            recycler.post {
                                                recycler.findViewHolderForAdapterPosition(targetPosition)
                                                    ?.itemView?.requestFocus()
                                            }
                                        }
                                    }
                                }
                                true
                            }
                        }
                    }
                    else -> false
                }
            }
        } else {
            holder.itemView.setOnKeyListener(null)
        }""",
            "estabilizar foco con pulsación prolongada en lista TV")

        text = replace_once(text,
            """        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_channel, parent, false)""",
            """        val layout = if (isTV) R.layout.item_channel_tv else R.layout.item_channel
        val view = LayoutInflater.from(parent.context).inflate(layout, parent, false)""",
            "elegir fila de canal XML")

        text = replace_once(text,
            "val logoRadius = if (isTV) 12 else (6 * itemView.resources.displayMetrics.density + 0.5f).toInt()",
            """val logoRadiusRes = if (isTV) R.dimen.channel_logo_corner_radius_tv else R.dimen.channel_logo_corner_radius_mobile
            val logoRadius = itemView.resources.getDimensionPixelSize(logoRadiusRes)""",
            "radio del logo desde dimens.xml")

        text = text.replace("import android.util.TypedValue\n", "")
        import re
        text, visual_init_count = re.subn(
            r"        init \{\n            val density = itemView.resources.displayMetrics.density\n.*?\n        \}\n\n        private var currentChannel: Channel\? = null",
            "        private var currentChannel: Channel? = null",
            text,
            count=1,
            flags=re.S,
        )
        if visual_init_count != 1:
            raise RuntimeError("No se pudo retirar la configuración visual de ChannelsAdapter.kt")

    elif name == "app/src/main/java/com/angulismotv/ui/InlinePlayerPresentationController.kt":
        text = replace_once(text, "        inlinePlayerContainer.visibility = View.VISIBLE\n        if (!isTV()) {\n", "        inlinePlayerContainer.visibility = View.VISIBLE\n        tvPlayerEmptyState?.visibility = View.GONE\n        if (!isTV()) {\n", "ocultar placeholder al seleccionar")

    elif name == "app/src/main/java/com/angulismotv/data/IptvOrgDataSource.kt":
        text = replace_once(text, "import java.net.URI\n", "import java.net.URI\nimport java.util.concurrent.TimeUnit\n", "importar límite de tiempo de catálogo")
        text = replace_once(text, "            val call = httpClient.newCall(request)\n", "            val call = httpClient.newCall(request).apply {\n                timeout().timeout(90, TimeUnit.SECONDS)\n            }\n", "limitar duración total de descarga M3U")

    elif name == "app/src/main/java/com/angulismotv/data/ChannelFeedDataSource.kt":
        text = replace_once(text, "import java.util.Locale\n", "import java.util.Locale\nimport java.util.concurrent.TimeUnit\n", "importar límite de tiempo de fuente JSON")
        text = replace_once(text, "            val call = httpClient.newCall(request)\n", "            val call = httpClient.newCall(request).apply {\n                timeout().timeout(90, TimeUnit.SECONDS)\n            }\n", "limitar duración total de descarga JSON")

    elif name == "app/src/main/java/com/angulismotv/data/ChannelFilterEngine.kt":
        text = replace_once(text,
            "    private val spanishLocale = Locale.forLanguageTag(\"es-AR\")\n",
            "    private val spanishLocale = Locale.forLanguageTag(\"es-AR\")\n    private val combiningMarksRegex = Regex(\"\\\\p{M}+\")\n    private val whitespaceRegex = Regex(\"\\\\s+\")\n",
            "reutilizar expresiones de normalización")
        text = replace_once(text,
            """    private fun normalizeCategory(raw: String): String = Normalizer
        .normalize(raw.trim().lowercase(Locale.ROOT), Normalizer.Form.NFD)
        .replace(Regex(\"\\\\p{M}+\"), \"\")
        .replace('_', ' ')
        .replace('-', ' ')
        .replace(Regex(\"\\\\s+\"), \" \")
        .trim()""",
            """    private fun normalizeCategory(raw: String): String = Normalizer
        .normalize(raw.trim().lowercase(Locale.ROOT), Normalizer.Form.NFD)
        .replace(combiningMarksRegex, \"\")
        .replace('_', ' ')
        .replace('-', ' ')
        .replace(whitespaceRegex, \" \")
        .trim()""", "normalizar categoría sin crear Regex repetidas")
        text = replace_once(text, ".split(Regex(\"\\\\s+\"))", ".split(whitespaceRegex)", "reutilizar normalización de nombres de categoría")

    elif name == "app/src/main/java/com/angulismotv/ui/PlayerChannelPanelController.kt":
        for old, new, label in [
            ("import androidx.core.content.ContextCompat\n", "import androidx.core.content.ContextCompat\nimport androidx.lifecycle.lifecycleScope\nimport kotlinx.coroutines.Dispatchers\nimport kotlinx.coroutines.Job\nimport kotlinx.coroutines.delay\nimport kotlinx.coroutines.launch\nimport kotlinx.coroutines.withContext\n", "imports coroutines panel"),
            ("    private var channelNumbersByIdentity: Map<String, Int> = emptyMap()\n", """    private var channelNumbersByIdentity: Map<String, Int> = emptyMap()
    private var catalogGeneration = 0
    private var channelListJob: Job? = null
    private var searchJob: Job? = null
    private var searchGeneration = 0
    private var preparedCatalog: List<Channel>? = null
    private var preparedCategoryItems: List<CategoriesAdapter.CategoryItem> = emptyList()
""", "estado de tareas del panel"),
        ]:
            text = replace_once(text, old, new, label)

        old_catalog = """    fun setChannelCatalog(channels: List<Channel>) {
        filteredChannels = channels
        channelNumbersByIdentity = ChannelCatalog.channelNumbersByIdentity(channels)
    }
"""
        new_catalog = """    fun setChannelCatalog(channels: List<Channel>) {
        filteredChannels = channels
        val requestGeneration = ++catalogGeneration
        searchGeneration++
        searchJob?.cancel()
        channelListJob?.cancel()
        preparedCatalog = null
        preparedCategoryItems = emptyList()
        channelNumbersByIdentity = emptyMap()
        val snapshot = channels

        activity.lifecycleScope.launch {
            val prepared = withContext(Dispatchers.Default) {
                val countsByCategory = snapshot.groupingBy {
                    ChannelFilterEngine.categoryKey(it.category)
                }.eachCount()
                val categoryItems = ChannelFilterEngine.availableCategories(snapshot).map { (key, label) ->
                    CategoriesAdapter.CategoryItem(key, label, countsByCategory[key] ?: 0)
                }
                Triple(ChannelCatalog.channelNumbersByIdentity(snapshot), categoryItems, snapshot)
            }
            if (requestGeneration != catalogGeneration || activity.isFinishing || activity.isDestroyed ||
                getChannels() !== snapshot) return@launch

            channelNumbersByIdentity = prepared.first
            preparedCategoryItems = prepared.second
            preparedCatalog = prepared.third
            if (isReady) {
                updateCategoriesList()
                updateChannelsList(scrollToSelected = true)
                if (isSearchActive) scheduleSearch(menuSearchInput.text.toString())
            }
        }
    }
"""
        if old_catalog in text:
            text = replace_once(text, old_catalog, new_catalog, "preparar catálogo del panel en segundo plano")
        elif "val requestGeneration = ++catalogGeneration" not in text or "preparedCatalog = null" not in text:
            raise RuntimeError("No se pudo aplicar preparar catálogo del panel en segundo plano: el código base no coincide.")

        old_categories = """    private fun updateCategoriesList() {
        val channels = getChannels()
        if (!isReady || channels.isEmpty()) return

        // Group source-specific labels (e.g. "Sports", "News", "Entertainment") into the
        // same concise category set used on the main screen. Count each group in one pass.
        val countsByCategory = channels.groupingBy {
            ChannelFilterEngine.categoryKey(it.category)
        }.eachCount()
        val items = ChannelFilterEngine.availableCategories(channels).map { (key, label) ->
            CategoriesAdapter.CategoryItem(
                key = key,
                name = label,
                count = countsByCategory[key] ?: 0
            )
        }
"""
        new_categories = """    private fun updateCategoriesList() {
        val channels = getChannels()
        if (!isReady || channels.isEmpty() || preparedCatalog !== channels) return

        // The category labels and counts were prepared once off the UI thread for this catalogue.
        val items = preparedCategoryItems
"""
        if old_categories in text:
            text = replace_once(text, old_categories, new_categories, "reutilizar metadatos de categorías")
        elif "val items = preparedCategoryItems" not in text:
            raise RuntimeError("No se pudo aplicar reutilizar metadatos de categorías: el código base no coincide.")

        old_list = """    private fun updateChannelsList(scrollToSelected: Boolean = false) {
        if (!isReady) return
        val channels = getChannels()
        filteredChannels = ChannelFilterEngine.filter(
            channels = channels,
            category = currentCategory,
            country = ChannelFilterEngine.ALL_COUNTRIES,
            query = ""
        )
        val current = getCurrentChannel()
        val selectedIndex = filteredChannels.indexOfFirst { current != null && ChannelIdentity.same(it, current) }
        sideChannelsAdapter.submitList(filteredChannels, selectedIndex)
        channelsCountText.text = filteredChannels.size.toString()
        if (scrollToSelected && selectedIndex >= 0) {
            channelsList.post {
                (channelsList.layoutManager as? LinearLayoutManager)?.scrollToPositionWithOffset(selectedIndex, 0)
            }
        }
    }
"""
        new_list = """    private fun updateChannelsList(scrollToSelected: Boolean = false) {
        if (!isReady) return
        val channels = getChannels()
        if (preparedCatalog !== channels) return
        val expectedCatalogGeneration = catalogGeneration
        val requestedCategory = currentCategory
        val current = getCurrentChannel()
        channelListJob?.cancel()
        channelListJob = activity.lifecycleScope.launch {
            val result = withContext(Dispatchers.Default) {
                ChannelFilterEngine.filter(
                    channels = channels,
                    category = requestedCategory,
                    country = ChannelFilterEngine.ALL_COUNTRIES,
                    query = ""
                )
            }
            if (expectedCatalogGeneration != catalogGeneration || requestedCategory != currentCategory ||
                channels !== getChannels() || isSearchActive || activity.isFinishing || activity.isDestroyed) {
                return@launch
            }
            filteredChannels = result
            val selectedIndex = result.indexOfFirst { current != null && ChannelIdentity.same(it, current) }
            sideChannelsAdapter.submitList(result, selectedIndex)
            channelsCountText.text = result.size.toString()
            if (scrollToSelected && selectedIndex >= 0) {
                channelsList.post {
                    if (expectedCatalogGeneration == catalogGeneration && requestedCategory == currentCategory) {
                        (channelsList.layoutManager as? LinearLayoutManager)?.scrollToPositionWithOffset(selectedIndex, 0)
                    }
                }
            }
        }
    }
"""
        if old_list in text:
            text = replace_once(text, old_list, new_list, "filtrar canales del panel fuera del hilo visual")
        elif "onUpdated: (() -> Unit)? = null" not in text or "sideChannelsAdapter.submitList(result, selectedIndex) {" not in text:
            raise RuntimeError("No se pudo aplicar filtrar canales del panel fuera del hilo visual: el código base no coincide.")

        old_after = """            override fun afterTextChanged(s: Editable?) {
                val query = s?.toString()?.trim()?.lowercase(Locale.ROOT).orEmpty()
                if (query.isNotEmpty()) {
                    val results = ChannelCatalog.searchByName(getChannels(), query)
                    searchAdapter.submitList(results)
                    channelsList.visibility = View.GONE
                    menuSearchResults.visibility = if (results.isNotEmpty()) View.VISIBLE else View.GONE
                    searchEmptyText.visibility = if (results.isEmpty()) View.VISIBLE else View.GONE
                    channelsCountText.text = results.size.toString()
                    contentTitle.text = "RESULTADOS: \\"$query\\""
                } else {
                    searchAdapter.submitList(emptyList())
                    menuSearchResults.visibility = View.GONE
                    searchEmptyText.visibility = View.GONE
                    channelsList.visibility = View.VISIBLE
                    contentTitle.text = "BUSCAR"
                    channelsCountText.text = ""
                }
            }
"""
        new_after = """            override fun afterTextChanged(s: Editable?) {
                scheduleSearch(s?.toString().orEmpty())
            }
"""
        text = replace_once(text, old_after, new_after, "buscar sin bloquear la interfaz")

        method_anchor = """    private fun updateCategoriesList() {
"""
        search_method = """    private fun scheduleSearch(rawQuery: String) {
        val query = rawQuery.trim()
        val requestGeneration = ++searchGeneration
        searchJob?.cancel()

        if (query.isEmpty()) {
            searchAdapter.submitList(emptyList())
            menuSearchResults.visibility = View.GONE
            searchEmptyText.visibility = View.GONE
            channelsList.visibility = View.VISIBLE
            contentTitle.text = if (isSearchActive) "BUSCAR" else contentTitle.text
            channelsCountText.text = if (isSearchActive) "" else filteredChannels.size.toString()
            return
        }

        // Keep input responsive while the previous query is cancelled and the new query settles.
        channelsList.visibility = View.GONE
        menuSearchResults.visibility = View.GONE
        searchEmptyText.visibility = View.GONE
        contentTitle.text = "BUSCAR"
        channelsCountText.text = ""

        val channels = getChannels()
        val expectedCatalogGeneration = catalogGeneration
        searchJob = activity.lifecycleScope.launch {
            delay(180)
            val results = withContext(Dispatchers.Default) {
                ChannelCatalog.searchByName(channels, query)
            }
            if (requestGeneration != searchGeneration || expectedCatalogGeneration != catalogGeneration ||
                !isSearchActive || channels !== getChannels() || activity.isFinishing || activity.isDestroyed) {
                return@launch
            }
            searchAdapter.submitList(results)
            menuSearchResults.visibility = if (results.isNotEmpty()) View.VISIBLE else View.GONE
            searchEmptyText.visibility = if (results.isEmpty()) View.VISIBLE else View.GONE
            channelsCountText.text = results.size.toString()
            contentTitle.text = "RESULTADOS: \\"$query\\""
        }
    }

"""
        if search_method.strip() not in text:
            text = replace_once(text, method_anchor, search_method + method_anchor, "agregar búsqueda asíncrona")

        text = replace_once(text,
            "        if (isSearchActive) deactivateSearchMode()\n        currentCategory = ALL_CHANNELS_CATEGORY",
            "        if (isSearchActive) deactivateSearchMode()\n        currentCategory = ALL_CHANNELS_CATEGORY",
            "normalizar selección de todos los canales")
        # Remove a duplicated guard that had no observable purpose in showAllChannels().
        text = text.replace(
            "        if (isSearchActive) deactivateSearchMode()\n        if (isSearchActive) deactivateSearchMode()\n",
            "        if (isSearchActive) deactivateSearchMode()\n"
        )
        # Keep the channel-number index off main, skip TV-only work on mobile, and restore focus
        # only after asynchronous list changes have committed.
        text = text.replace("import java.util.Locale\n", "")
        text = replace_once(text,
            "    private var preparedCategoryItems: List<CategoriesAdapter.CategoryItem> = emptyList()\n",
            "    private var preparedCategoryItems: List<CategoriesAdapter.CategoryItem> = emptyList()\n    private var pendingOpeningFocus = false\n",
            "recordar foco pendiente del panel")
        text = replace_once(text,
            """    fun setChannelCatalog(channels: List<Channel>) {
        filteredChannels = channels
        val requestGeneration = ++catalogGeneration""",
            """    fun setChannelCatalog(channels: List<Channel>) {
        filteredChannels = channels
        if (!isReady) {
            preparedCatalog = channels
            preparedCategoryItems = emptyList()
            channelNumbersByIdentity = emptyMap()
            return
        }
        val requestGeneration = ++catalogGeneration""", "evitar preparar panel TV en móviles")
        text = replace_once(text,
            """            if (isReady) {
                updateCategoriesList()
                updateChannelsList(scrollToSelected = true)
                if (isSearchActive) scheduleSearch(menuSearchInput.text.toString())
            }""",
            """            if (isReady) {
                if (pendingOpeningFocus) {
                    refreshForOpening()
                } else {
                    updateCategoriesList()
                    updateChannelsList(scrollToSelected = true)
                    if (isSearchActive) scheduleSearch(menuSearchInput.text.toString())
                }
            }""", "restaurar apertura del panel tras preparar el catálogo")
        text = replace_once(text,
            """    fun refreshForOpening() {
        if (!isReady) return
        updateCategoriesList()
        updateChannelsList(scrollToSelected = true)
        updateContentTitle()
        onFocusChannels()
    }""",
            """    fun refreshForOpening() {
        if (!isReady) return
        if (preparedCatalog !== getChannels()) {
            pendingOpeningFocus = true
            updateContentTitle()
            return
        }
        pendingOpeningFocus = false
        updateCategoriesList()
        updateContentTitle()
        updateChannelsList(scrollToSelected = true, onUpdated = onFocusChannels)
    }""", "esperar al catálogo antes de enfocar el panel")
        text = replace_once(text,
            """    fun deactivateSearchMode() {
        if (!isSearchActive) return""",
            """    fun deactivateSearchMode() {
        pendingOpeningFocus = false
        if (!isSearchActive) return""", "cancelar foco pendiente al cerrar búsqueda o panel")

        old_async_list = """    private fun updateChannelsList(scrollToSelected: Boolean = false) {
        if (!isReady) return
        val channels = getChannels()
        if (preparedCatalog !== channels) return
        val expectedCatalogGeneration = catalogGeneration
        val requestedCategory = currentCategory
        val current = getCurrentChannel()
        channelListJob?.cancel()
        channelListJob = activity.lifecycleScope.launch {
            val result = withContext(Dispatchers.Default) {
                ChannelFilterEngine.filter(
                    channels = channels,
                    category = requestedCategory,
                    country = ChannelFilterEngine.ALL_COUNTRIES,
                    query = ""
                )
            }
            if (expectedCatalogGeneration != catalogGeneration || requestedCategory != currentCategory ||
                channels !== getChannels() || isSearchActive || activity.isFinishing || activity.isDestroyed) {
                return@launch
            }
            filteredChannels = result
            val selectedIndex = result.indexOfFirst { current != null && ChannelIdentity.same(it, current) }
            sideChannelsAdapter.submitList(result, selectedIndex)
            channelsCountText.text = result.size.toString()
            if (scrollToSelected && selectedIndex >= 0) {
                channelsList.post {
                    if (expectedCatalogGeneration == catalogGeneration && requestedCategory == currentCategory) {
                        (channelsList.layoutManager as? LinearLayoutManager)?.scrollToPositionWithOffset(selectedIndex, 0)
                    }
                }
            }
        }
    }
"""
        new_async_list = """    private fun updateChannelsList(
        scrollToSelected: Boolean = false,
        onUpdated: (() -> Unit)? = null
    ) {
        if (!isReady) return
        val channels = getChannels()
        if (preparedCatalog !== channels) return
        val expectedCatalogGeneration = catalogGeneration
        val requestedCategory = currentCategory
        channelListJob?.cancel()
        channelListJob = activity.lifecycleScope.launch {
            val result = withContext(Dispatchers.Default) {
                ChannelFilterEngine.filter(
                    channels = channels,
                    category = requestedCategory,
                    country = ChannelFilterEngine.ALL_COUNTRIES,
                    query = ""
                )
            }
            if (expectedCatalogGeneration != catalogGeneration || requestedCategory != currentCategory ||
                channels !== getChannels() || isSearchActive || activity.isFinishing || activity.isDestroyed) {
                return@launch
            }

            filteredChannels = result
            val current = getCurrentChannel()
            val selectedIndex = result.indexOfFirst { current != null && ChannelIdentity.same(it, current) }
            channelsCountText.text = result.size.toString()
            sideChannelsAdapter.submitList(result, selectedIndex) {
                val stillCurrent = expectedCatalogGeneration == catalogGeneration &&
                    requestedCategory == currentCategory && channels === getChannels() &&
                    !isSearchActive && !activity.isFinishing && !activity.isDestroyed
                if (stillCurrent) {
                    if (scrollToSelected && selectedIndex >= 0) {
                        channelsList.post {
                            val stillCurrentAfterLayout = expectedCatalogGeneration == catalogGeneration &&
                                requestedCategory == currentCategory && channels === getChannels() && !isSearchActive
                            if (stillCurrentAfterLayout) {
                                (channelsList.layoutManager as? LinearLayoutManager)
                                    ?.scrollToPositionWithOffset(selectedIndex, 0)
                                onUpdated?.invoke()
                            }
                        }
                    } else {
                        onUpdated?.invoke()
                    }
                }
            }
        }
    }
"""
        text = replace_once(text, old_async_list, new_async_list, "esperar al commit del panel para actualizar foco")
        text = replace_once(text,
            """    private fun onCategorySelected(categoryKey: String) {
        deactivateSearchMode()
        currentCategory = categoryKey
        updateContentTitle()
        updateCategoriesList()
        updateChannelsList(scrollToSelected = true)
        updateAllChannelsSelection()
        onFocusChannels()
    }""",
            """    private fun onCategorySelected(categoryKey: String) {
        deactivateSearchMode()
        currentCategory = categoryKey
        updateContentTitle()
        updateCategoriesList()
        updateAllChannelsSelection()
        updateChannelsList(scrollToSelected = true, onUpdated = onFocusChannels)
    }""", "coordinar foco tras cambiar categoría")
        text = replace_once(text,
            """    private fun showAllChannels() {
        if (isSearchActive) deactivateSearchMode()
        currentCategory = ALL_CHANNELS_CATEGORY
        updateContentTitle()
        updateCategoriesList()
        updateChannelsList(scrollToSelected = true)
        updateAllChannelsSelection()
        onFocusChannels()
    }""",
            """    private fun showAllChannels() {
        if (isSearchActive) deactivateSearchMode()
        currentCategory = ALL_CHANNELS_CATEGORY
        updateContentTitle()
        updateCategoriesList()
        updateAllChannelsSelection()
        updateChannelsList(scrollToSelected = true, onUpdated = onFocusChannels)
    }""", "coordinar foco al mostrar todos los canales")
        text = replace_once(text,
            "val index = getChannels().indexOfFirst { ChannelIdentity.same(it, channel) }",
            "val index = channelNumbersByIdentity[ChannelIdentity.key(channel)]?.minus(1)\n                    ?: getChannels().indexOfFirst { ChannelIdentity.same(it, channel) }",
            "usar índice O(1) al elegir resultado de búsqueda")

    elif name == "app/src/main/java/com/angulismotv/adapters/SideChannelsAdapter.kt":
        # If the side adapter was already transformed in an earlier CI run, skip its one-time
        # structural rewrite and only apply the tiny selection-number correction if still needed.
        if "private val differ = AsyncListDiffer(this, object : DiffUtil.ItemCallback<Channel>() {" in text:
            text = text.replace(
                "        fun updateSelection(channel: Channel, isSelected: Boolean, channelNumber: Int) {\n            itemView.isSelected = isSelected",
                "        fun updateSelection(channel: Channel, isSelected: Boolean, channelNumber: Int) {\n            number.text = if (channelNumber > 0) channelNumber.toString() else \"—\"\n            itemView.isSelected = isSelected",
                1
            )
            return text.encode("utf-8")
        text = replace_once(text,
            "import androidx.recyclerview.widget.DiffUtil\n",
            "import androidx.recyclerview.widget.AsyncListDiffer\nimport androidx.recyclerview.widget.DiffUtil\n",
            "importar actualización diferencial asíncrona")
        text = replace_once(text,
            "import com.angulismotv.models.Channel\n",
            "import com.angulismotv.models.Channel\nimport com.angulismotv.models.ChannelIdentity\n",
            "importar identidad de selección")
        old_adapter = """    private var channels: List<Channel> = emptyList()
    private var selectedIndex: Int = -1

    fun submitList(newChannels: List<Channel>, selectedIdx: Int) {
        val oldChannels = channels
        val oldSelected = selectedIndex
        val nextChannels = newChannels.toList()
        val nextSelected = selectedIdx

        val diff = DiffUtil.calculateDiff(object : DiffUtil.Callback() {
            override fun getOldListSize() = oldChannels.size
            override fun getNewListSize() = nextChannels.size

            override fun areItemsTheSame(oldPosition: Int, newPosition: Int): Boolean =
                oldChannels[oldPosition].name == nextChannels[newPosition].name &&
                    oldChannels[oldPosition].logo == nextChannels[newPosition].logo

            override fun areContentsTheSame(oldPosition: Int, newPosition: Int): Boolean {
                val oldChannel = oldChannels[oldPosition]
                val newChannel = nextChannels[newPosition]
                val oldWasSelected = oldPosition == oldSelected
                val newIsSelected = newPosition == nextSelected
                return oldChannel == newChannel && oldWasSelected == newIsSelected
            }
        })

        channels = nextChannels
        selectedIndex = nextSelected
        diff.dispatchUpdatesTo(this)
    }
"""
        new_adapter = """    private val differ = AsyncListDiffer(this, object : DiffUtil.ItemCallback<Channel>() {
        override fun areItemsTheSame(oldItem: Channel, newItem: Channel): Boolean =
            oldItem.name == newItem.name && oldItem.logo == newItem.logo

        override fun areContentsTheSame(oldItem: Channel, newItem: Channel): Boolean =
            oldItem == newItem
    })
    private var selectedChannelKey: String? = null

    fun submitList(
        newChannels: List<Channel>,
        selectedIdx: Int,
        onCommitted: (() -> Unit)? = null
    ) {
        val snapshot = newChannels.toList()
        selectedChannelKey = snapshot.getOrNull(selectedIdx)?.let(ChannelIdentity::key)
        differ.submitList(snapshot) {
            // Selection is presentation state; update visible row payloads after the background diff.
            if (itemCount > 0) notifyItemRangeChanged(0, itemCount, PAYLOAD_SELECTION_STATE)
            onCommitted?.invoke()
        }
    }
"""
        text = replace_once(text, old_adapter, new_adapter, "mover DiffUtil del panel a AsyncListDiffer")
        text = replace_once(text,
            "        val channel = channels[position]\n        holder.bind(channel, position == selectedIndex, channelNumber(channel))",
            "        val channel = differ.currentList[position]\n        holder.bind(channel, ChannelIdentity.key(channel) == selectedChannelKey, channelNumber(channel))",
            "leer filas desde AsyncListDiffer")
        text = replace_once(text,
            "                channels.getOrNull(currentPosition)?.let { currentChannel ->",
            "                differ.currentList.getOrNull(currentPosition)?.let { currentChannel ->",
            "proteger clics ante actualización asíncrona")
        text = replace_once(text, "    override fun getItemCount() = channels.size\n", "    override fun getItemCount() = differ.currentList.size\n", "consultar lista diferencial")
        text = replace_once(text,
            """    class ViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {""",
            """    override fun onBindViewHolder(holder: ViewHolder, position: Int, payloads: MutableList<Any>) {
        if (payloads.isNotEmpty() && payloads.all { it == PAYLOAD_SELECTION_STATE }) {
            differ.currentList.getOrNull(position)?.let { channel ->
                holder.updateSelection(
                    channel,
                    ChannelIdentity.key(channel) == selectedChannelKey,
                    channelNumber(channel)
                )
            }
            return
        }
        onBindViewHolder(holder, position)
    }

    companion object {
        private const val PAYLOAD_SELECTION_STATE = "selection_state"
    }

    class ViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {""",
            "actualizar selección mediante payload")
        text = replace_once(text,
            """            itemView.isSelected = isSelected
            marker.visibility = if (isSelected) View.VISIBLE else View.INVISIBLE
            name.text = channel.name
            optionsIndicator.visibility = if (!channel.options.isNullOrEmpty()) View.VISIBLE else View.GONE
            itemView.setBackgroundResource(
                if (isSelected) R.drawable.side_channel_item_selected
                else R.drawable.side_channel_item_bg
            )
            itemView.contentDescription = buildString {
                if (channelNumber > 0) append("Canal $channelNumber: ")
                append(channel.name)
                if (!channel.options.isNullOrEmpty()) append(", con opciones")
                if (isSelected) append(", en reproducción")
            }
            // Mantiene la forma original de cada logo; el elemento no agrega una tarjeta detrás.
            logo.loadChannelLogo(channel.name, channel.logo)
        }
""",
            """            name.text = channel.name
            optionsIndicator.visibility = if (!channel.options.isNullOrEmpty()) View.VISIBLE else View.GONE
            updateSelection(channel, isSelected, channelNumber)
            // Mantiene la forma original de cada logo; el elemento no agrega una tarjeta detrás.
            logo.loadChannelLogo(channel.name, channel.logo)
        }

        fun updateSelection(channel: Channel, isSelected: Boolean, channelNumber: Int) {
            number.text = if (channelNumber > 0) channelNumber.toString() else "—"
            itemView.isSelected = isSelected
            marker.visibility = if (isSelected) View.VISIBLE else View.INVISIBLE
            itemView.setBackgroundResource(
                if (isSelected) R.drawable.side_channel_item_selected
                else R.drawable.side_channel_item_bg
            )
            itemView.contentDescription = buildString {
                if (channelNumber > 0) append("Canal $channelNumber: ")
                append(channel.name)
                if (!channel.options.isNullOrEmpty()) append(", con opciones")
                if (isSelected) append(", en reproducción")
            }
        }
""", "reutilizar render de selección")


    elif name == "app/src/main/java/com/angulismotv/ui/ChannelScreenLayoutController.kt":
        text = replace_once(text,
            "        channelsSectionHeader.visibility = View.VISIBLE\n        channelsSearchContainer.visibility = View.GONE\n        onSearchVisibilityChanged(false)\n",
            "        channelsSectionHeader.visibility = View.GONE\n        channelsSearchContainer.visibility = View.GONE\n        categoriesScroll.visibility = View.GONE\n        searchInput.nextFocusUpId = com.angulismotv.R.id.tv_inline_search_button\n        searchInput.nextFocusLeftId = com.angulismotv.R.id.tv_inline_search_button\n        searchInput.nextFocusDownId = com.angulismotv.R.id.channels_recycler\n        channelsRecycler.nextFocusUpId = com.angulismotv.R.id.tv_inline_search_button\n        channelsRecycler.descendantFocusability = ViewGroup.FOCUS_AFTER_DESCENDANTS\n        onSearchVisibilityChanged(false)\n",
            "ocultar categorías de pantalla TV y enlazar foco del buscador")

    elif name == "app/src/main/java/com/angulismotv/ui/ChannelCategoryBarController.kt":
        text = replace_once(text, "    private var selectedCategoryFocusViewId: Int = View.NO_ID\n", "    private var selectedCategoryFocusViewId: Int = View.NO_ID\n    private var availableCountryKeys: List<String> = emptyList()\n", "guardar países preparados")
        text = replace_once(text, "        selectedCategoryFocusViewId = View.NO_ID\n    }\n\n    fun render() {\n        val categories = ChannelFilterEngine.availableCategories(getChannels())\n", "        selectedCategoryFocusViewId = View.NO_ID\n        availableCountryKeys = emptyList()\n    }\n\n    fun render(\n        preparedCategories: List<Pair<String, String>>? = null,\n        preparedCountries: List<String>? = null\n    ) {\n        val categories = (preparedCategories ?: ChannelFilterEngine.availableCategories(getChannels()))\n", "render categorías preparadas")
        text = replace_once(text, "            .ifEmpty { listOf(ChannelFilterEngine.ALL_COUNTRIES to \"Todos\") }\n        container.removeAllViews()\n", "            .ifEmpty { listOf(ChannelFilterEngine.ALL_COUNTRIES to \"Todos\") }\n        if (preparedCountries != null) availableCountryKeys = preparedCountries\n        container.removeAllViews()\n", "guardar países preparados")
        text = replace_once(text, "        val countries = ChannelFilterEngine.availableCountries(getChannels())\n", "        val countries = availableCountryKeys.ifEmpty { ChannelFilterEngine.availableCountries(getChannels()) }\n", "reutilizar países")

    elif name == "app/src/main/java/com/angulismotv/ui/DebouncedChannelSearchController.kt":
        text = replace_once(text, "const val DEFAULT_DELAY_MS = 300L", "const val DEFAULT_DELAY_MS = 180L", "reducir latencia de búsqueda")

    elif name == "app/src/main/java/com/angulismotv/data/ChannelCatalog.kt":
        text = replace_once(text,
'''            terms.all { it in searchableText } ||
                searchableText.replace(" ", "").contains(compactQuery)
''',
'''            val tokens = searchableText.split(' ')
            terms.all { term ->
                tokens.any { token -> token.startsWith(term) || (term.length >= 3 && token.contains(term)) }
            } || searchableText.replace(" ", "").contains(compactQuery)
''', "buscar por prefijos y fragmentos")

    elif name == "app/src/main/java/com/angulismotv/UnifiedPlayerActivity.kt":
        text = replace_once(text,
            "            currentChannelIndex = index\n            currentChannel = channel\n            loadChannelInfo(channel)\n",
            "            currentChannelIndex = index\n            currentChannel = channel\n            getSharedPreferences(\"angulismotv_playback\", MODE_PRIVATE).edit()\n                .putString(\"last_channel_key\", ChannelIdentity.key(channel))\n                .putString(\"last_channel_name\", channel.name)\n                .putString(\"last_channel_logo\", channel.logo)\n                .apply()\n            loadChannelInfo(currentChannel!!)\n",
            "recordar el último canal en fullscreen")
        # El zapping conserva solo el escudo; no muestra texto ni número junto al nombre.
        import re
        zapping_name_pattern = re.compile(
            r"        zappingChannelName\?\.apply \{\n.*?        \}\n",
            re.S
        )
        text, zapping_name_matches = zapping_name_pattern.subn(
            "        zappingChannelName?.visibility = View.GONE\n",
            text,
            count=1
        )
        if zapping_name_matches == 0 and "zappingChannelName?.visibility = View.GONE" not in text:
            raise RuntimeError("No se pudo ocultar el nombre transitorio del zapping.")

        # Primero preparar estado invisible y después animar; evitar destellos y reinicios.
        reveal_helpers = """    private fun revealControlView(target: View, slide: Boolean) {
        target.animate().cancel()
        if (target.visibility != View.VISIBLE) {
            target.alpha = 0f
            target.translationY = if (slide) 12f * resources.displayMetrics.density else 0f
            target.visibility = View.VISIBLE
        }
        target.animate()
            .alpha(1f)
            .translationY(0f)
            .setDuration(230L)
            .setInterpolator(android.view.animation.DecelerateInterpolator(1.35f))
            .withEndAction {
                if (target.visibility == View.VISIBLE) {
                    target.alpha = 1f
                    target.translationY = 0f
                }
            }
            .start()
    }

    private fun concealControlView(target: View, slide: Boolean) {
        if (target.visibility != View.VISIBLE) return
        target.animate().cancel()
        target.animate()
            .alpha(0f)
            .translationY(if (slide) 10f * resources.displayMetrics.density else 0f)
            .setDuration(150L)
            .setInterpolator(android.view.animation.AccelerateInterpolator())
            .withEndAction {
                target.visibility = View.GONE
                target.alpha = 1f
                target.translationY = 0f
            }
            .start()
    }

"""
        if "    private fun revealControlView(target: View, slide: Boolean)" not in text:
            text = replace_once(
                text,
                "    private fun showControls() {",
                reveal_helpers + "    private fun showControls() {",
                "añadir transiciones suaves a los controles"
            )

        def replace_in_method(source: str, start_marker: str, end_marker: str, old: str, new: str, label: str) -> str:
            start = source.find(start_marker)
            end = source.find(end_marker, start + len(start_marker))
            if start < 0 or end < 0:
                raise RuntimeError("No se encontró el método para " + label)
            region = source[start:end]
            region = replace_once(region, old, new, label)
            return source[:start] + region + source[end:]

        visible_pair = "        controlsOverlay.visibility = View.VISIBLE\n        bottomControls.visibility = View.VISIBLE\n"
        reveal_pair = "        revealControlView(controlsOverlay, slide = false)\n        revealControlView(bottomControls, slide = true)\n"
        text = replace_in_method(
            text, "    private fun showControls() {", "    private fun showControlsTemporarily() {",
            visible_pair, reveal_pair, "mostrar controles"
        )
        text = replace_in_method(
            text, "    private fun showControlsTemporarily() {", "    private fun hideControls() {",
            visible_pair, reveal_pair, "mostrar controles temporales"
        )
        text = replace_in_method(
            text, "    private fun hideControls() {", "    private fun updatePlayerTimeline() {",
            "        controlsOverlay.visibility = View.GONE\n        bottomControls.visibility = View.GONE\n",
            "        concealControlView(controlsOverlay, slide = false)\n        concealControlView(bottomControls, slide = true)\n",
            "ocultar controles"
        )

    elif name == "app/src/main/java/com/angulismotv/MainActivity.kt":
        text = replace_once(text,
            "    private fun loadAllChannels() {\n        val generation = ++channelLoadGeneration\n        channelLoadJob?.cancel()\n",
            "    private fun loadAllChannels() {\n        if (channelLoadJob?.isActive == true) {\n            Log.d(TAG, \"Se omite una recarga duplicada: ya hay una carga en curso\")\n            return\n        }\n        val generation = ++channelLoadGeneration\n",
            "evitar recargas simultáneas")
        text = replace_once(text,
            "            try {\n                val result = ChannelRepository.loadAll()\n",
            "            try {\n                if (lastLoadResult == null) {\n                    val cached = ChannelRepository.loadCached(this@MainActivity)\n                    if (cached != null && generation == channelLoadGeneration && !isFinishing && !isDestroyed) {\n                        allChannels = cached.channels\n                        lastLoadResult = cached\n                        fragmentChannels.showResult(cached)\n                        Log.d(TAG, \"Catálogo local mostrado de inmediato: \" + cached.channels.size + \" canales\")\n                    }\n                }\n                val fresh = ChannelRepository.loadAll(this@MainActivity)\n",
            "mostrar caché al inicio")
        text = replace_once(text,
            "                if (generation != channelLoadGeneration || isFinishing || isDestroyed) return@launch\n                allChannels = result.channels\n",
            "                if (generation != channelLoadGeneration || isFinishing || isDestroyed) return@launch\n                val result = if (fresh.channels.isEmpty() && allChannels.isNotEmpty() &&\n                    (fresh.failed || fresh.partialFailure)) {\n                    Log.w(TAG, \"Falló la actualización; se conserva el último catálogo válido\")\n                    LoadResult(allChannels, partialFailure = true, sourceName = \"Caché local\")\n                } else fresh\n                allChannels = result.channels\n",
            "conservar catálogo ante fallo de red")
        text = replace_once(text,
            "                val result = LoadResult(emptyList(), failed = true)\n                allChannels = emptyList()\n",
            "                val result = if (allChannels.isNotEmpty()) {\n                    LoadResult(allChannels, partialFailure = true, sourceName = \"Caché local\")\n                } else LoadResult(emptyList(), failed = true)\n",
            "conservar catálogo ante excepción")

    elif name == "app/src/main/java/com/angulismotv/models/Channel.kt":
        text = replace_once(text, "import kotlinx.parcelize.Parcelize\n", "import kotlinx.parcelize.Parcelize\nimport com.google.gson.annotations.SerializedName\n", "importar anotaciones Gson")
        for field in ["name", "logo", "streamUrl", "streamType", "options", "show", "category", "country"]:
            text = replace_once(text, "    val " + field + ":", "    @field:SerializedName(\"" + field + "\") val " + field + ":", "serializar campo Channel " + field)
        # StreamOption also uses the same stable JSON names, but those fields appear a second time.
        start = text.index("data class StreamOption(")
        head, tail = text[:start], text[start:]
        for field in ["name", "iframe", "streamType"]:
            tail = replace_once(tail, "    val " + field + ":", "    @field:SerializedName(\"" + field + "\") val " + field + ":", "serializar StreamOption " + field)
        text = head + tail

    elif name == "app/src/main/res/layout/fragment_channels.xml":
        text = replace_once(text, '        android:keepScreenOn="true"\n        android:visibility="gone">\n', '        android:keepScreenOn="true"\n        android:visibility="visible">\n', "mantener mini reproductor visible")
        marker = '''        <ProgressBar
            android:id="@+id/inline_progress_bar"
'''
        placeholder = '''        <LinearLayout
            android:id="@+id/tv_player_empty_state"
            android:layout_width="match_parent"
            android:layout_height="match_parent"
            android:orientation="vertical"
            android:gravity="center"
            android:padding="12dp"
            android:background="@drawable/bg_tv_player_idle"
            android:visibility="visible"
            android:clickable="false"
            android:focusable="false">

            <ImageView
                android:layout_width="32dp"
                android:layout_height="32dp"
                android:layout_marginBottom="7dp"
                android:src="@drawable/ic_play"
                android:contentDescription=""
                android:scaleType="fitCenter"
                android:tint="@color/accent" />

            <TextView
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:gravity="center"
                android:text="@string/tv_player_empty_title"
                android:textColor="@color/text_primary"
                android:textSize="14sp"
                android:fontFamily="sans-serif-medium"
                android:maxLines="1" />

            <TextView
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_marginTop="3dp"
                android:gravity="center"
                android:text="Elegí un canal para reproducirlo"
                android:textColor="@color/text_secondary"
                android:textSize="11sp"
                android:maxLines="1" />
        </LinearLayout>

'''
        text = replace_once(text, marker, placeholder + marker, "placeholder del mini reproductor")

    elif name == "app/src/main/res/layout/fragment_channels_tv.xml":
        import xml.etree.ElementTree as ET
        android_ns = "{http://schemas.android.com/apk/res/android}"
        app_ns = "{http://schemas.android.com/apk/res-auto}"
        ET.register_namespace("android", android_ns[1:-1])
        ET.register_namespace("app", app_ns[1:-1])
        root = ET.fromstring(text)

        def by_id(view_id: str):
            suffix = "/" + view_id
            return next((node for node in root.iter()
                         if node.get(android_ns + "id", "").endswith(suffix)), None)

        # Fondo medianoche con matices nebulares sutiles; no añade textura sobre el vídeo.
        root.set(android_ns + "background", "@drawable/bg_nebula_screen")
        player_column = by_id("tv_player_column")
        player = by_id("inline_player_container")
        panel = by_id("tv_channels_panel")
        categories = by_id("categories_scroll")
        search = by_id("channels_search_container")
        header = by_id("channels_section_header")
        if any(node is None for node in (player_column, player, panel, categories, search, header)):
            raise RuntimeError("No se pudieron localizar todos los componentes del layout Android TV.")

        player_column.set(android_ns + "layout_weight", "2.15")
        panel.set(android_ns + "layout_weight", "1")
        panel.set(android_ns + "paddingTop", "4dp")
        # La lista se integra al fondo: sin marco exterior ni sombra de tarjeta.
        panel.set(android_ns + "background", "@android:color/transparent")
        panel.set(android_ns + "elevation", "0dp")
        panel.attrib.pop(android_ns + "backgroundTint", None)
        header.set(android_ns + "visibility", "gone")
        categories.set(android_ns + "visibility", "gone")

        if search in list(panel):
            panel.remove(search)
        search.set(android_ns + "layout_width", "320dp")
        search.set(android_ns + "layout_height", "wrap_content")
        search.set(android_ns + "layout_gravity", "top|end")
        search.set(android_ns + "layout_marginTop", "12dp")
        search.set(android_ns + "layout_marginEnd", "12dp")
        search.set(android_ns + "visibility", "gone")
        search.set(android_ns + "elevation", "9dp")

        search_button = by_id("tv_inline_search_button")
        if search_button is None:
            search_button = ET.Element("ImageButton", {
                android_ns + "id": "@+id/tv_inline_search_button",
                android_ns + "layout_width": "44dp",
                android_ns + "layout_height": "44dp",
                android_ns + "layout_gravity": "top|end",
                android_ns + "layout_marginTop": "12dp",
                android_ns + "layout_marginEnd": "12dp",
                android_ns + "background": "@drawable/bg_inline_player_control",
                android_ns + "contentDescription": "Buscar canales",
                android_ns + "focusable": "true",
                android_ns + "focusableInTouchMode": "true",
                android_ns + "clickable": "true",
                android_ns + "elevation": "6dp",
                android_ns + "nextFocusDown": "@id/channels_recycler",
                android_ns + "nextFocusRight": "@id/channels_recycler",
                android_ns + "nextFocusLeft": "@id/inline_player_container",
                android_ns + "src": "@drawable/ic_search",
                app_ns + "tint": "@color/text_primary"
            })
            player.append(search_button)
        if search not in list(player):
            player.append(search)

        text = ET.tostring(root, encoding="unicode", xml_declaration=True)


    # Ajustes transversales de controles del reproductor (móvil y TV).
    if name.startswith("app/src/main/res/layout/") and name.endswith(".xml") and any(token in name.lower() for token in ("player", "fullscreen", "transmision")):
        import xml.etree.ElementTree as ET
        android_ns = "{http://schemas.android.com/apk/res/android}"
        ET.register_namespace("android", android_ns[1:-1])
        ET.register_namespace("app", "http://schemas.android.com/apk/res-auto")
        try:
            root = ET.fromstring(text)
        except ET.ParseError:
            root = None
        if root is not None:
            def norm_attr(node, key):
                return (node.get(android_ns + key, "") or "").lower().replace("_", " ").replace("-", " ")
            # Favoritos está implementado: no ocultar ni colapsar ese control.
            # El control de salida debe comunicar volver/salir, no cerrar algo ambiguo.
            for node in root.iter():
                identity = (node.get(android_ns + "id", "") + " " +
                            norm_attr(node, "contentDescription") + " " +
                            norm_attr(node, "tooltipText")).lower()
                if any(word in identity for word in ("close", "cerrar", "exit", "salir")):
                    if node.tag.split("}")[-1] in ("ImageButton", "ImageView"):
                        src = node.get(android_ns + "src", "")
                        if "close" in src or "cross" in src or "cerrar" in src:
                            node.set(android_ns + "src", "@drawable/ic_arrow_back")
                        node.set(android_ns + "contentDescription", "Salir del reproductor")
            if name.endswith("activity_unified_player.xml"):
                for node in root.iter():
                    if node.get(android_ns + "id", "").endswith("/zapping_channel_name"):
                        node.set(android_ns + "visibility", "gone")
            text = ET.tostring(root, encoding="unicode", xml_declaration=True)

    text = apply_nebula_visuals(name, text)
    text = apply_ui_redesign(name, text)
    return text.encode("utf-8")


def apply_ui_redesign(name: str, text: str) -> str:
    """Apply the TV interface refinements after the existing ZIP overlays."""
    if name == "app/src/main/java/com/angulismotv/MainActivity.kt":
        old = """        // La búsqueda no ocupa espacio fijo en la lista: se abre desde este acceso de cabecera.
        binding.headerSearchButton.visibility = View.VISIBLE"""
        new = """        // En Android TV la búsqueda se abre desde el acceso bajo el reproductor.
        binding.headerSearchButton.visibility = View.GONE
        binding.headerSearchButton.isFocusable = false
        binding.headerSearchButton.isFocusableInTouchMode = false"""
        text = replace_once(text, old, new, "ocultar búsqueda de cabecera en TV")

    elif name == "app/src/main/java/com/angulismotv/fragments/ChannelsFragment.kt":
        old_click = """        if (isTV) {
            view?.findViewById<View>(R.id.tv_inline_search_button)?.setOnClickListener {
                toggleSearchFromHeader()
            }
        }"""
        new_click = """        if (isTV) {
            view?.findViewById<View>(R.id.tv_inline_channels_button)?.apply {
                isFocusable = true
                isFocusableInTouchMode = true
                setOnClickListener { openPlayerPanelShortcut(openSearch = false) }
            }
            view?.findViewById<View>(R.id.tv_inline_search_button)?.apply {
                isFocusable = true
                isFocusableInTouchMode = true
                setOnClickListener { openPlayerPanelShortcut(openSearch = true) }
            }
        }"""
        text = replace_once(text, old_click, new_click, "conectar accesos del panel de TV")

        old_nav = """        inlinePlayerContainer.nextFocusLeftId = R.id.menu_channels
        inlinePlayerContainer.nextFocusRightId = R.id.channels_recycler
        inlinePlayerContainer.nextFocusUpId = R.id.header_search_button"""
        new_nav = """        inlinePlayerContainer.nextFocusLeftId = R.id.menu_channels
        inlinePlayerContainer.nextFocusRightId = R.id.channels_recycler
        inlinePlayerContainer.nextFocusUpId = R.id.menu_channels
        inlinePlayerContainer.nextFocusDownId = R.id.tv_inline_channels_button"""
        text = replace_once(text, old_nav, new_nav, "actualizar navegación del foco desde el reproductor")

        old_signature = "    private fun launchPlayerActivity(channel: Channel, fromInline: Boolean) {"
        new_signature = """    private fun openPlayerPanelShortcut(openSearch: Boolean) {
        if (!isTV || !isAdded) return
        val channel = inlineChannel ?: originalChannels.firstOrNull {
            !it.streamUrl.isNullOrBlank() || !it.options.isNullOrEmpty()
        }
        if (channel == null) {
            Toast.makeText(requireContext(), "No hay canales disponibles para abrir el reproductor", Toast.LENGTH_SHORT).show()
            return
        }

        // Solo transferir la sesión integrada si existe un canal ya seleccionado.
        val reuseInlineSession = inlineChannel != null && ChannelIdentity.same(inlineChannel!!, channel)
        launchPlayerActivity(
            channel = channel,
            fromInline = reuseInlineSession,
            openChannelPanel = true,
            openChannelSearch = openSearch
        )
    }

    private fun launchPlayerActivity(
        channel: Channel,
        fromInline: Boolean,
        openChannelPanel: Boolean = false,
        openChannelSearch: Boolean = false
    ) {"""
        text = replace_once(text, old_signature, new_signature, "añadir acceso directo al panel del reproductor")

        old_intent = "        val launchIntent = createPlayerLaunchIntent(channel, catalog, catalogToken, fromInline, handoff)"
        new_intent = """        val launchIntent = createPlayerLaunchIntent(channel, catalog, catalogToken, fromInline, handoff)
            .putExtra("open_channel_panel", openChannelPanel)
            .putExtra("open_channel_search", openChannelSearch)"""
        text = replace_once(text, old_intent, new_intent, "enviar destino inicial al reproductor")

        # Keep the inline-to-fullscreen ownership transfer outside the Fragment.
        text = replace_once(
            text,
            "from com.angulismotv.player.InlinePlayerHandoff\n",
            "from com.angulismotv.player.InlinePlayerHandoff\n"
            "import com.angulismotv.player.InlinePlayerTransferController\n"
            "import com.angulismotv.player.InlinePlayerTransferPlan\n",
            "importar controlador de traspaso"
        )
        text = replace_once(
            text,
            "    private var inlinePlaybackEngineController: InlinePlaybackEngineController? = null\n",
            "    private var inlinePlaybackEngineController: InlinePlaybackEngineController? = null\n"
            "    private var inlinePlayerTransferController: InlinePlayerTransferController? = null\n",
            "registrar controlador de traspaso"
        )
        text = replace_once(
            text,
            "private data class InlineHandoffPlan(\n"
            "    val transferNativePlayer: Boolean,\n"
            "    val transferWebView: Boolean\n"
            ")\n\n",
            "",
            "retirar plan de traspaso local"
        )
        text = replace_once(
            text,
            "        setupInlinePlaybackEngine()\n        applyChannelScreenLayout(view)",
            "        setupInlinePlaybackEngine()\n"
            "        setupInlinePlayerTransferController()\n"
            "        applyChannelScreenLayout(view)",
            "inicializar controlador de traspaso"
        )
        text = replace_once(
            text,
            "    private fun applyChannelScreenLayout(view: View) {\n",
            "    private fun setupInlinePlayerTransferController() {\n"
            "        inlinePlayerTransferController = InlinePlayerTransferController(\n"
            "            playerProvider = { inlineExoPlayer },\n"
            "            streamUrlProvider = { inlineCurrentStreamUrl },\n"
            "            streamTypeProvider = { inlineCurrentStreamType },\n"
            "            sourceIndexProvider = { inlineSourceIndex },\n"
            "            channelProvider = { inlineChannel },\n"
            "            webView = inlineWebView,\n"
            "            recoveryProvider = { inlineRecoveryController },\n"
            "            playbackEngineProvider = { inlinePlaybackEngineController },\n"
            "            setLaunchingFullscreen = { isLaunchingFullscreen = it }\n"
            "        )\n"
            "    }\n\n"
            "    private fun applyChannelScreenLayout(view: View) {\n",
            "configurar controlador de traspaso"
        )
        text = replace_once(
            text,
            "        val handoff = prepareInlineHandoff(channel, fromInline)\n",
            "        val handoff = inlinePlayerTransferController?.prepare(channel, fromInline)\n"
            "            ?: InlinePlayerTransferPlan.NONE\n",
            "delegar decisión de traspaso"
        )
        old_handoff = """    private fun prepareInlineHandoff(channel: Channel, fromInline: Boolean): InlineHandoffPlan {
        isLaunchingFullscreen = fromInline
        inlineRecoveryController?.stopWatchdog()
        inlineRecoveryController?.cancelStablePlaybackTimer()
        inlineRecoveryController?.cancelPendingReconnect()
        val currentPlayer = inlineExoPlayer
        val transferNativePlayer = fromInline && currentPlayer != null &&
            inlineCurrentStreamUrl.isNotBlank() && inlineCurrentStreamType != StreamType.IFRAME
        val transferWebView = fromInline && currentPlayer == null &&
            inlineCurrentStreamType == StreamType.IFRAME && inlineCurrentStreamUrl.isNotBlank() &&
            inlineWebView.visibility == View.VISIBLE && inlineWebView.url != null

        when {
            transferNativePlayer && currentPlayer != null -> offerNativePlayerToFullscreen(channel, currentPlayer)
            transferWebView -> offerWebViewToFullscreen(channel)
            else -> inlineExoPlayer?.pause()
        }
        inlineWebView.onPause()
        return InlineHandoffPlan(transferNativePlayer, transferWebView)
    }

    private fun offerNativePlayerToFullscreen(channel: Channel, player: ExoPlayer) {
        val session = InlinePlayerHandoff.Session(
            player = player,
            channel = inlineChannel ?: channel,
            streamUrl = inlineCurrentStreamUrl,
            streamType = inlineCurrentStreamType,
            sourceIndex = inlineSourceIndex,
            wasPlaying = player.playWhenReady
        )
        inlinePlaybackEngineController?.detachForHandoff(player)
        InlinePlayerHandoff.offerToFullscreen(session)
    }

    private fun offerWebViewToFullscreen(channel: Channel) {
        val oldParent = inlineWebView.parent as? ViewGroup
        val oldIndex = oldParent?.indexOfChild(inlineWebView) ?: -1
        val oldParams = inlineWebView.layoutParams
        // Re-parent the live iframe WebView instead of loading it in a second instance.
        oldParent?.removeView(inlineWebView)
        InlinePlayerHandoff.offerToFullscreen(
            InlinePlayerHandoff.Session(
                player = null,
                channel = inlineChannel ?: channel,
                streamUrl = inlineCurrentStreamUrl,
                streamType = StreamType.IFRAME,
                sourceIndex = inlineSourceIndex,
                wasPlaying = true,
                webView = inlineWebView,
                webViewParentIndex = oldIndex,
                webViewLayoutParams = oldParams
            )
        )
    }

"""
        text = replace_once(text, old_handoff, "", "extraer implementación del traspaso")
        text = replace_once(
            text,
            "        inlinePlaybackEngineController = null\n        inlineTimelineController = null\n",
            "        inlinePlaybackEngineController = null\n"
            "        inlinePlayerTransferController = null\n"
            "        inlineTimelineController = null\n",
            "liberar controlador de traspaso"
        )

    elif name == "app/src/main/java/com/angulismotv/UnifiedPlayerActivity.kt":
        old = "        channelPanelController.setChannelCatalog(allChannels)"
        new = """        channelPanelController.setChannelCatalog(allChannels)
        if (isTV && intent.getBooleanExtra("open_channel_panel", false)) {
            val openSearchOnStart = intent.getBooleanExtra("open_channel_search", false)
            playerContainer.post {
                if (isFinishing || isDestroyed || !isTV) return@post
                openSidePanel()
                if (openSearchOnStart) channelPanelController.activateSearchMode()
            }
        }"""
        text = replace_once(text, old, new, "abrir panel o búsqueda según acceso de TV")

    elif name == "app/src/main/res/layout/activity_main.xml":
        import xml.etree.ElementTree as ET
        android_ns = "{http://schemas.android.com/apk/res/android}"
        ET.register_namespace("android", android_ns[1:-1])
        ET.register_namespace("app", "http://schemas.android.com/apk/res-auto")
        root = ET.fromstring(text)
        app_ns = "{http://schemas.android.com/apk/res-auto}"
        for view_id in ("menu_channels", "menu_agenda"):
            suffix = "/" + view_id
            item = next((node for node in root.iter()
                         if node.get(android_ns + "id", "").endswith(suffix)), None)
            if item is None:
                raise RuntimeError("No se encontró el elemento del menú lateral: " + view_id)
            # El icono marca la sección activa; el fondo neutro marca dónde está el foco.
            item.set(android_ns + "background", "@drawable/bg_tv_rail_item")
            item.set(android_ns + "stateListAnimator", "@null")
            item.set(android_ns + "focusable", "true")
            item.set(android_ns + "focusableInTouchMode", "true")
            item.set(android_ns + "clickable", "true")
        bottom_nav = next((node for node in root.iter()
                           if node.get(android_ns + "id", "").endswith("/bottom_navigation")), None)
        if bottom_nav is not None:
            bottom_nav.set(app_ns + "itemIconTint", "@color/bottom_nav_icon_tint")
            bottom_nav.set(app_ns + "itemTextColor", "@color/bottom_nav_text_tint")
        text = ET.tostring(root, encoding="unicode", xml_declaration=True)

    elif name == "app/src/main/res/layout/fragment_channels_tv.xml":
        import xml.etree.ElementTree as ET
        android_ns = "{http://schemas.android.com/apk/res/android}"
        app_ns = "{http://schemas.android.com/apk/res-auto}"
        ET.register_namespace("android", android_ns[1:-1])
        ET.register_namespace("app", app_ns[1:-1])
        root = ET.fromstring(text)

        def by_id(view_id: str):
            suffix = "/" + view_id
            return next((node for node in root.iter()
                         if node.get(android_ns + "id", "").endswith(suffix)), None)

        player_column = by_id("tv_player_column")
        player = by_id("inline_player_container")
        channels_panel = by_id("tv_channels_panel")
        channels_list = by_id("channels_list_container")
        if any(node is None for node in (player_column, player, channels_panel, channels_list)):
            raise RuntimeError("Faltan componentes del layout Android TV para aplicar el rediseño.")
        # También limpiar la lista y su marco interno si el ZIP base les asigna un drawable.
        channels_panel.set(android_ns + "background", "@android:color/transparent")
        channels_panel.set(android_ns + "elevation", "0dp")
        channels_panel.attrib.pop(android_ns + "backgroundTint", None)
        channels_list.set(android_ns + "background", "@android:color/transparent")
        channels_list.set(android_ns + "elevation", "0dp")
        channels_list.attrib.pop(android_ns + "backgroundTint", None)

        # Dos atajos discretos debajo de la vista previa; reutilizan la Activity de pantalla completa.
        action_row = by_id("tv_player_action_row")
        if action_row is None:
            action_row = ET.Element("LinearLayout", {
                android_ns + "id": "@+id/tv_player_action_row",
                android_ns + "layout_width": "match_parent",
                android_ns + "layout_height": "wrap_content",
                android_ns + "layout_marginTop": "8dp",
                android_ns + "orientation": "horizontal",
                android_ns + "gravity": "start|center_vertical",
                android_ns + "minHeight": "48dp",
                android_ns + "paddingStart": "2dp",
                android_ns + "paddingEnd": "2dp",
                android_ns + "clipChildren": "false",
                android_ns + "clipToPadding": "false"
            })
        if action_row in list(player_column):
            player_column.remove(action_row)
        children = list(player_column)
        player_index = children.index(player)
        player_column.insert(player_index + 1, action_row)

        channels_button = by_id("tv_inline_channels_button")
        if channels_button is None:
            channels_button = ET.Element("ImageButton", {
                android_ns + "id": "@+id/tv_inline_channels_button"
            })
        search_button = by_id("tv_inline_search_button")
        if search_button is None:
            search_button = ET.Element("ImageButton", {
                android_ns + "id": "@+id/tv_inline_search_button"
            })

        # El botón de búsqueda preexistente se mueve desde la esquina del vídeo a esta fila.
        for button in (channels_button, search_button):
            for parent in root.iter():
                if button in list(parent):
                    parent.remove(button)
                    break

        def configure_action_button(button, view_id: str, description: str, icon: str):
            attrs = {
                android_ns + "id": "@+id/" + view_id,
                android_ns + "layout_width": "48dp",
                android_ns + "layout_height": "48dp",
                android_ns + "layout_marginTop": "0dp",
                android_ns + "layout_marginEnd": "10dp" if view_id == "tv_inline_channels_button" else "0dp",
                android_ns + "background": "@android:color/transparent",
                android_ns + "contentDescription": description,
                android_ns + "focusable": "true",
                android_ns + "focusableInTouchMode": "true",
                android_ns + "clickable": "true",
                android_ns + "padding": "12dp",
                android_ns + "nextFocusUp": "@id/inline_player_container",
                android_ns + "nextFocusDown": "@id/channels_recycler",
                android_ns + "nextFocusLeft": "@id/menu_channels" if view_id == "tv_inline_channels_button" else "@id/tv_inline_channels_button",
                android_ns + "nextFocusRight": "@id/tv_inline_search_button" if view_id == "tv_inline_channels_button" else "@id/channels_recycler",
                android_ns + "src": icon,
                app_ns + "tint": "@color/bottom_nav_color",
                android_ns + "visibility": "visible"
            }
            button.attrib.clear()
            button.attrib.update(attrs)
            button.attrib.pop(android_ns + "layout_gravity", None)

        configure_action_button(channels_button, "tv_inline_channels_button", "Abrir lista de canales", "@drawable/ic_menu")
        configure_action_button(search_button, "tv_inline_search_button", "Buscar canales", "@drawable/ic_search")
        action_row.append(channels_button)
        action_row.append(search_button)

        # La guía textual permanente se reemplaza por controles limpios y accesibles.
        for view_id in ("tv_player_guide", "tv_player_keys_hint", "tv_player_footer_hint"):
            node = by_id(view_id)
            if node is not None:
                node.set(android_ns + "visibility", "gone")

        # La lista derecha queda sin cabecera ni bloque de instrucciones; las flechas son solo visuales.
        arrows = {}
        for view_id, symbol in (("tv_channels_scroll_up", "▲"), ("tv_channels_scroll_down", "▼")):
            arrow = by_id(view_id)
            if arrow is None:
                arrow = ET.Element("TextView", {
                    android_ns + "id": "@+id/" + view_id
                })
            for parent in root.iter():
                if arrow in list(parent):
                    parent.remove(arrow)
                    break
            arrow.attrib.update({
                android_ns + "layout_width": "match_parent",
                android_ns + "layout_height": "18dp",
                android_ns + "gravity": "center",
                android_ns + "text": symbol,
                android_ns + "textColor": "@color/text_hint",
                android_ns + "textSize": "12sp",
                android_ns + "includeFontPadding": "false",
                android_ns + "focusable": "false",
                android_ns + "clickable": "false",
                android_ns + "importantForAccessibility": "no"
            })
            arrows[view_id] = arrow

        up_arrow = arrows["tv_channels_scroll_up"]
        down_arrow = arrows["tv_channels_scroll_down"]
        channels_panel.insert(list(channels_panel).index(channels_list), up_arrow)
        channels_panel.insert(list(channels_panel).index(channels_list) + 1, down_arrow)

        guide = by_id("tv_list_guide")
        if guide is not None:
            guide.set(android_ns + "visibility", "gone")
            panel_children = list(channels_panel)
            guide_index = panel_children.index(guide)
            if guide_index > 0:
                divider = panel_children[guide_index - 1]
                if divider.tag == "View" and divider.get(android_ns + "layout_height") == "1dp":
                    divider.set(android_ns + "visibility", "gone")

        text = ET.tostring(root, encoding="unicode", xml_declaration=True)

    return text




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
                data = overlays.get(name, source.read(name))
                data = apply_source_optimizations(name, data)
                target.writestr(info, data)
                if name in overlays:
                    written.add(name)
            for name, content in overlays.items():
                if name not in written:
                    target.writestr(name, apply_source_optimizations(name, content), compress_type=zipfile.ZIP_DEFLATED)
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
