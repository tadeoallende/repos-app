package com.angulismotv.ui

import android.content.Context
import android.content.res.Configuration
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.FrameLayout
import android.widget.LinearLayout
import com.angulismotv.R

/**
 * Owns the responsive arrangement of the fullscreen player's control rows.
 * On phones the native transport trio sits over the video center; TV keeps it in the bottom row.
 */
class PlayerControlsLayoutController(
    private val context: Context,
    private val isTV: Boolean,
    private val playerControlsMainRow: LinearLayout,
    private val playerChannelIdentity: LinearLayout,
    private val playerActionGroupsRow: LinearLayout,
    private val playerTransportControls: LinearLayout,
    private val playerUtilityControls: LinearLayout,
    private val bottomControls: View,
    private val centerTransportControlsContainer: FrameLayout
) {
    fun apply(orientation: Int = context.resources.configuration.orientation) {
        positionTransportControls(centered = !isTV)

        val compactPortrait = !isTV && orientation == Configuration.ORIENTATION_PORTRAIT
        val identityParams = playerChannelIdentity.layoutParams as LinearLayout.LayoutParams
        val actionParams = playerActionGroupsRow.layoutParams as LinearLayout.LayoutParams
        val utilityParams = playerUtilityControls.layoutParams as LinearLayout.LayoutParams
        val transportParams = playerTransportControls.layoutParams as? LinearLayout.LayoutParams

        if (compactPortrait) {
            playerControlsMainRow.orientation = LinearLayout.VERTICAL
            identityParams.width = ViewGroup.LayoutParams.MATCH_PARENT
            identityParams.weight = 0f
            identityParams.marginEnd = 0
            playerChannelIdentity.layoutParams = identityParams
            actionParams.width = ViewGroup.LayoutParams.MATCH_PARENT
            actionParams.height = ViewGroup.LayoutParams.WRAP_CONTENT
            playerActionGroupsRow.layoutParams = actionParams
            transportParams?.let {
                it.marginStart = 0
                playerTransportControls.layoutParams = it
            }
            utilityParams.marginStart = dimen(R.dimen.player_control_spacing_compact)
            playerUtilityControls.layoutParams = utilityParams
            bottomControls.setPadding(
                dimen(R.dimen.player_controls_horizontal_padding_compact),
                dimen(R.dimen.player_controls_padding_top),
                dimen(R.dimen.player_controls_horizontal_padding_compact),
                dimen(R.dimen.player_controls_padding_bottom)
            )
        } else {
            playerControlsMainRow.orientation = LinearLayout.HORIZONTAL
            identityParams.width = 0
            identityParams.weight = 1f
            identityParams.marginEnd = 0
            playerChannelIdentity.layoutParams = identityParams
            actionParams.width = ViewGroup.LayoutParams.WRAP_CONTENT
            actionParams.height = ViewGroup.LayoutParams.WRAP_CONTENT
            playerActionGroupsRow.layoutParams = actionParams
            transportParams?.let {
                it.marginStart = dimen(R.dimen.player_control_spacing_regular)
                playerTransportControls.layoutParams = it
            }
            utilityParams.marginStart = dimen(R.dimen.player_control_spacing_regular)
            playerUtilityControls.layoutParams = utilityParams
            bottomControls.setPadding(
                dimen(R.dimen.player_controls_horizontal_padding_wide),
                dimen(R.dimen.player_controls_padding_top),
                dimen(R.dimen.player_controls_horizontal_padding_wide),
                dimen(R.dimen.player_controls_padding_bottom)
            )
        }
    }

    private fun positionTransportControls(centered: Boolean) {
        val target: ViewGroup = if (centered) centerTransportControlsContainer else playerActionGroupsRow
        val current = playerTransportControls.parent as? ViewGroup
        if (current !== target) {
            current?.removeView(playerTransportControls)
            if (centered) {
                target.addView(
                    playerTransportControls,
                    FrameLayout.LayoutParams(
                        ViewGroup.LayoutParams.WRAP_CONTENT,
                        ViewGroup.LayoutParams.WRAP_CONTENT,
                        Gravity.CENTER
                    )
                )
            } else {
                target.addView(
                    playerTransportControls,
                    0,
                    LinearLayout.LayoutParams(
                        ViewGroup.LayoutParams.WRAP_CONTENT,
                        ViewGroup.LayoutParams.WRAP_CONTENT
                    )
                )
            }
        }

        if (centered) {
            playerTransportControls.layoutParams = FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT,
                ViewGroup.LayoutParams.WRAP_CONTENT,
                Gravity.CENTER
            )
            playerTransportControls.gravity = Gravity.CENTER
        } else {
            val params = playerTransportControls.layoutParams as? LinearLayout.LayoutParams
                ?: LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.WRAP_CONTENT,
                    ViewGroup.LayoutParams.WRAP_CONTENT
                )
            params.marginStart = dimen(R.dimen.player_control_spacing_regular)
            playerTransportControls.layoutParams = params
            playerTransportControls.gravity = Gravity.CENTER_VERTICAL
        }
    }

    private fun dimen(resourceId: Int): Int = context.resources.getDimensionPixelSize(resourceId)
}
