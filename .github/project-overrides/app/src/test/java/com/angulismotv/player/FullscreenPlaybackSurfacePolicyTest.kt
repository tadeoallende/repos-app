package com.angulismotv.player

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class FullscreenPlaybackSurfacePolicyTest {
    @Test
    fun nativePlayerRequestsDirectionalFocusOnlyOnTv() {
        assertTrue(FullscreenPlaybackSurfacePolicy.shouldRequestNativeFocus(isTV = true))
        assertFalse(FullscreenPlaybackSurfacePolicy.shouldRequestNativeFocus(isTV = false))
    }
}
