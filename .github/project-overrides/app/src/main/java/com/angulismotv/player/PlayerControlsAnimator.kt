package com.angulismotv.player

import android.view.View
import android.view.animation.AccelerateInterpolator
import android.view.animation.DecelerateInterpolator

/**
 * Encapsula las transiciones de visibilidad de los controles del reproductor.
 *
 * Mantiene el comportamiento visual existente sin que la Activity gestione directamente
 * alpha, desplazamientos, duraciones ni callbacks de fin de animación.
 */
internal class PlayerControlsAnimator {

    fun show(target: View, slide: Boolean) {
        target.animate().cancel()
        if (target.visibility != View.VISIBLE) {
            target.alpha = 0f
            target.translationY = if (slide) 12f * target.resources.displayMetrics.density else 0f
            target.visibility = View.VISIBLE
        }
        target.animate()
            .alpha(1f)
            .translationY(0f)
            .setDuration(SHOW_DURATION_MS)
            .setInterpolator(DecelerateInterpolator(1.35f))
            .withEndAction {
                if (target.visibility == View.VISIBLE) {
                    target.alpha = 1f
                    target.translationY = 0f
                }
            }
            .start()
    }

    fun hide(target: View, slide: Boolean) {
        if (target.visibility != View.VISIBLE) return
        target.animate().cancel()
        target.animate()
            .alpha(0f)
            .translationY(if (slide) 10f * target.resources.displayMetrics.density else 0f)
            .setDuration(HIDE_DURATION_MS)
            .setInterpolator(AccelerateInterpolator())
            .withEndAction {
                target.visibility = View.GONE
                target.alpha = 1f
                target.translationY = 0f
            }
            .start()
    }

    private companion object {
        const val SHOW_DURATION_MS = 230L
        const val HIDE_DURATION_MS = 150L
    }
}
