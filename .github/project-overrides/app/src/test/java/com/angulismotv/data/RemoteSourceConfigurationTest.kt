package com.angulismotv.data

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class RemoteSourceConfigurationTest {
    @Test
    fun differentConfigurationEndpointsDoNotShareTheSameCacheEntry() {
        val productionUrl = "https://raw.githubusercontent.com/tadeoallende/repos-app/refs/heads/main/fuentes.json"
        val testUrl = "https://raw.githubusercontent.com/tadeoallende/repos-app/refs/heads/chatgpt/prueba-acceso-2026-10-21-3/fuentes.json"

        assertTrue(
            RemoteSourceConfiguration.cacheKeyFor(productionUrl) !=
                RemoteSourceConfiguration.cacheKeyFor(testUrl)
        )
    }

    @Test
    fun surroundingWhitespaceDoesNotCreateASecondCacheEntry() {
        val url = "https://example.com/fuentes.json"

        assertEquals(
            RemoteSourceConfiguration.cacheKeyFor(url),
            RemoteSourceConfiguration.cacheKeyFor("  $url  ")
        )
    }
}
