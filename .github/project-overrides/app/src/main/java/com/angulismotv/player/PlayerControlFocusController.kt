package com.angulismotv.player

import android.view.View

/**
 * Centraliza el orden y la navegación horizontal del foco para los controles del reproductor.
 * La Activity conserva la gestión del mando y pasa el estado mutable mediante proveedores.
 */
internal class PlayerControlFocusController(
    private val isTv: () -> Boolean,
    private val controlsVisible: () -> Boolean,
    private val isPanelOpen: () -> Boolean,
    private val lastFocusedControlId: () -> Int,
    private val playerContainer: View,
    private val controlsProvider: () -> List<View>,
    private val resetAutoHideTimer: () -> Unit
) {

    fun visibleControls(): List<View> = controlsProvider().filter {
        it.visibility == View.VISIBLE && it.isFocusable && it.isEnabled
    }

    fun updateControlFocusOrder() {
        if (!isTv()) return
        val controls = visibleControls()
        controls.forEachIndexed { index, control ->
            control.nextFocusLeftId = controls.getOrNull(index - 1)?.id ?: View.NO_ID
            control.nextFocusRightId = controls.getOrNull(index + 1)?.id ?: View.NO_ID
        }
    }

    fun requestPreferredControlFocus() {
        if (!isTv() || !controlsVisible() || isPanelOpen()) return
        val controls = visibleControls()
        if (controls.isEmpty()) {
            playerContainer.requestFocus()
            return
        }
        val preferred = controls.firstOrNull { it.id == lastFocusedControlId() } ?: controls.first()
        preferred.requestFocus()
    }

    fun navigateRight() {
        val controls = visibleControls()
        if (controls.isEmpty()) return
        val index = controls.indexOfFirst { it.hasFocus() }
        controls.getOrNull(if (index < 0) 0 else (index + 1).coerceAtMost(controls.lastIndex))?.requestFocus()
        resetAutoHideTimer()
    }

    fun navigateLeft() {
        val controls = visibleControls()
        if (controls.isEmpty()) return
        val index = controls.indexOfFirst { it.hasFocus() }
        controls.getOrNull(if (index < 0) 0 else (index - 1).coerceAtLeast(0))?.requestFocus()
        resetAutoHideTimer()
    }
}
