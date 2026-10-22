#!/usr/bin/env python3
"""Apply tracked source overlays to the Android project ZIP before GitHub Actions builds it."""
from __future__ import annotations
import os
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
        text = replace_once(text, old_categories, new_categories, "metadatos de categorías asíncronos")
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

    elif name == "app/src/main/java/com/angulismotv/adapters/ChannelsAdapter.kt":
        text = replace_once(text, "if (isTV && itemCount > 0) notifyItemRangeChanged(0, itemCount, PAYLOAD_PREVIEW_STATE)", "if (itemCount > 0) notifyItemRangeChanged(0, itemCount, PAYLOAD_PREVIEW_STATE)", "notificar selección móvil")
        text = replace_once(text, "holder.itemView.isSelected = isTV && previewChannelKey == ChannelIdentity.key(channel)", "holder.itemView.isSelected = previewChannelKey == ChannelIdentity.key(channel)", "selección visual móvil")
        text = replace_once(text, "holder.itemView.isSelected = isTV && channel != null &&\n                previewChannelKey == ChannelIdentity.key(channel)", "holder.itemView.isSelected = channel != null && previewChannelKey == ChannelIdentity.key(channel)", "selección por payload")

    elif name == "app/src/main/java/com/angulismotv/ui/InlinePlayerPresentationController.kt":
        text = replace_once(text, "        inlinePlayerContainer.visibility = View.VISIBLE\n        if (!isTV()) {\n", "        inlinePlayerContainer.visibility = View.VISIBLE\n        tvPlayerEmptyState?.visibility = View.GONE\n        if (!isTV()) {\n", "ocultar placeholder al seleccionar")

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
        text = replace_once(text, old_catalog, new_catalog, "preparar catálogo del panel en segundo plano")

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
        text = replace_once(text, old_categories, new_categories, "reutilizar metadatos de categorías")

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
        text = replace_once(text, old_list, new_list, "filtrar canales del panel fuera del hilo visual")

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

    return text.encode("utf-8")



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
