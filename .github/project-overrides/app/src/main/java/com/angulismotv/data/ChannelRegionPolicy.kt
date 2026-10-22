package com.angulismotv.data

import com.angulismotv.models.Channel
import java.text.Normalizer
import java.util.Locale

/** Regional policy for the public IPTV-org catalogue. Personal JSON feeds intentionally bypass it. */
object ChannelRegionPolicy {
    private val americasCountryCodes = setOf(
        // North, Central and South America, the Caribbean, and associated territories.
        "ag", "ai", "ar", "aw", "bb", "bl", "bm", "bo", "bq", "br", "bs", "bz", "ca", "cl", "co", "cr",
        "cu", "cw", "dm", "do", "ec", "fk", "gd", "gf", "gl", "gp", "gs", "gt", "gy", "hn",
        "ht", "jm", "kn", "ky", "lc", "mf", "mq", "ms", "mx", "ni", "pa", "pe", "pm", "pr",
        "py", "sr", "sv", "sx", "tc", "tt", "us", "uy", "vc", "ve", "vg", "vi"
    )

    private val knownAmericanCountryNames: Set<String> by lazy {
        val english = Locale.ENGLISH
        val spanish = Locale.forLanguageTag("es-AR")
        americasCountryCodes.flatMap { code ->
            val countryLocale = Locale.Builder().setRegion(code.uppercase(Locale.ROOT)).build()
            listOf(
                countryLocale.getDisplayCountry(english),
                countryLocale.getDisplayCountry(spanish),
                code
            ).filter(String::isNotBlank).map(::normalize)
        }.toSet() + setOf(
            "usa", "eeuu", "estados unidos", "estados unidos de america",
            "united states", "united states of america", "canada", "argentina",
            "brasil", "brazil", "mexico", "mexico", "méxico"
        )
    }

    private val internationalNetworkPatterns = listOf(
        Regex("\\bbbc (news|world|world news|world service)\\b"),
        Regex("\\bcnn( international| intl)?\\b"),
        Regex("\\bdeutsche welle\\b"),
        Regex("\\bdw (english|espanol|español|news|noticias)\\b"),
        Regex("\\bfrance 24\\b"),
        Regex("\\bal jazeera\\b"),
        Regex("\\beuronews\\b"),
        Regex("\\bcgtn( documentary| news| spanish| francais| france)?\\b"),
        Regex("\\bnhk world( japan)?\\b"),
        Regex("\\btrt world\\b"),
        Regex("\\btv5 monde\\b"),
        Regex("\\bsky news( international)?\\b"),
        Regex("\\bbloomberg( television| tv)?\\b"),
        Regex("\\bcnbc( international| world)?\\b"),
        Regex("\\bwion\\b"),
        Regex("\\barirang( world)?\\b"),
        Regex("\\bchannel news asia\\b"),
        Regex("\\bi24news\\b"),
        Regex("\\brt international\\b"),
        Regex("\\brussia today\\b"),
        Regex("\\bafrica news\\b"),
        Regex("\\btelesur\\b"),
        Regex("\\bcanal 24 horas\\b"),
        Regex("\\bunited nations( tv)?\\b"),
        Regex("\\bmtv(\\s+(europe|asia|music|hits|live|hd))?\\b"),
        Regex("\\bdiscovery( channel| science| turbo| world| family| kids)?\\b"),
        Regex("\\b(national geographic|nat geo( wild)?)\\b"),
        Regex("\\banimal planet\\b"),
        Regex("\\bcartoon network\\b"),
        Regex("\\bcartoonito\\b"),
        Regex("\\bboomerang\\b"),
        Regex("\\bnickelodeon\\b"),
        Regex("\\bnick jr\\b"),
        Regex("\\bdisney (channel|junior|xd)\\b"),
        Regex("\\b(espn|eurosport)(\\s+[0-9]+| deportes| international)?\\b"),
        Regex("\\bfox (sports|news|business|crime|life)\\b"),
        Regex("\\bmsnbc\\b"),
        Regex("\\b(nbc|cbs|abc) news\\b"),
        Regex("\\bhbo\\b"),
        Regex("\\bcinemax\\b"),
        Regex("\\baxn\\b"),
        Regex("\\bparamount (network|channel)\\b"),
        Regex("\\bwarner tv\\b"),
        Regex("\\b(star (plus|world|gold|sports))\\b"),
        Regex("\\bsony entertainment television\\b"),
        Regex("\\bzee (tv|cinema|world|business)\\b"),
        Regex("\\b(tlc|vh1|travel channel|comedy central)\\b"),
        Regex("\\bhistory( channel| 2)?\\b"),
        Regex("\\ba e\\b"),
        Regex("\\buniversal (channel|tv)\\b"),
        Regex("\\bbbc (earth|brit|lifestyle|first|america)\\b"),
        Regex("\\btve internacional\\b"),
        Regex("\\brai (italia|international)\\b"),
        Regex("\\bsky sports\\b")
    )

    /** Keep American channels, explicitly international categories, and recognized global networks. */
    fun shouldKeep(channel: Channel): Boolean =
        isFromAmericas(channel.country) || isInternationalNetwork(channel)

    fun filter(channels: List<Channel>): List<Channel> = channels.filter(::shouldKeep)

    fun isFromAmericas(rawCountry: String): Boolean {
        val value = rawCountry.trim().substringBefore(',')
        if (value.isBlank()) return false
        val key = normalize(value)
        return key in americasCountryCodes || key in knownAmericanCountryNames
    }

    fun isInternationalNetwork(channel: Channel): Boolean {
        if (ChannelFilterEngine.categoryKey(channel.category) == "internacionales") return true
        val name = normalize(channel.name)
        return internationalNetworkPatterns.any { it.containsMatchIn(name) }
    }

    // Reuse compiled patterns: normalization runs for every channel during catalogue filtering.
    private val combiningMarksPattern = Regex("\\p{M}+")
    private val nonWordCharactersPattern = Regex("[^\\p{L}\\p{N}]+")

    private fun normalize(value: String): String = Normalizer
        .normalize(value.lowercase(Locale.ROOT), Normalizer.Form.NFD)
        .replace(combiningMarksPattern, "")
        .replace(nonWordCharactersPattern, " ")
        .trim()
}
