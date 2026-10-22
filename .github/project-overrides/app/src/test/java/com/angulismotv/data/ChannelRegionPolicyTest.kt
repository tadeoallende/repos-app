package com.angulismotv.data

import com.angulismotv.models.Channel
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ChannelRegionPolicyTest {
    @Test
    fun keepsNorthCentralSouthAmericanAndCaribbeanCountries() {
        listOf("ar", "ca", "us", "mx", "cr", "br", "cl", "pr", "United States", "México")
            .forEach { country -> assertTrue("country=$country", ChannelRegionPolicy.isFromAmericas(country)) }
    }

    @Test
    fun excludesCountriesOutsideTheAmericas() {
        listOf("gb", "fr", "jp", "es", "de", "United Kingdom", "France").forEach { country ->
            assertFalse("country=$country", ChannelRegionPolicy.isFromAmericas(country))
        }
    }

    @Test
    fun keepsRecognizedInternationalNetworksOutsideTheAmericas() {
        val channels = listOf(
            Channel(name = "BBC News", country = "gb"),
            Channel(name = "France 24 English", country = "fr"),
            Channel(name = "NHK World Japan", country = "jp"),
            Channel(name = "DW Español", country = "de")
        )
        assertEquals(channels.size, ChannelRegionPolicy.filter(channels).size)
    }

    @Test
    fun keepsExplicitInternationalCategoryAndExcludesUnrelatedForeignChannel() {
        val international = Channel(name = "Servicio Mundial", country = "gb", category = "International")
        val foreignRegional = Channel(name = "Local London TV", country = "gb", category = "General")
        assertTrue(ChannelRegionPolicy.shouldKeep(international))
        assertFalse(ChannelRegionPolicy.shouldKeep(foreignRegional))
    }

    @Test
    fun doesNotAssumeUnknownCountryIsAmerican() {
        assertFalse(ChannelRegionPolicy.shouldKeep(Channel(name = "Unknown Channel")))
    }
}
