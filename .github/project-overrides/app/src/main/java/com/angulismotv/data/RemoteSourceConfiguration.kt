package com.angulismotv.data

import android.content.Context
import android.util.Log
import com.angulismotv.BuildConfig
import com.google.gson.JsonParser
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.net.HttpURLConnection
import java.net.URL

/** Downloads a remote source configuration and caches the last valid version for offline fallback. */
internal object RemoteSourceConfiguration {
    data class PrimarySource(val enabled: Boolean, val name: String, val url: String)

    private const val TAG = "RemoteSourceConfig"
    private const val PREFS_NAME = "remote_source_configuration"
    private const val PREFS_KEY = "last_valid_json"
    private const val CONNECT_TIMEOUT_MS = 5_000
    private const val READ_TIMEOUT_MS = 7_000

    suspend fun load(context: Context?): PrimarySource = withContext(Dispatchers.IO) {
        val fallback = fromBuildConfig()
        if (context == null || BuildConfig.REMOTE_SOURCES_CONFIG_URL.isBlank()) return@withContext fallback
        val preferences = context.applicationContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val remoteJson = runCatching { download(BuildConfig.REMOTE_SOURCES_CONFIG_URL.trim()) }
            .onFailure { Log.w(TAG, "No se pudo actualizar la configuración remota; se usará la última válida") }
            .getOrNull()

        if (!remoteJson.isNullOrBlank()) {
            val parsed = parse(remoteJson)
            if (parsed != null) {
                preferences.edit().putString(PREFS_KEY, remoteJson).apply()
                return@withContext parsed
            }
            Log.w(TAG, "Configuración remota inválida; se usará la última válida")
        }
        preferences.getString(PREFS_KEY, null)?.let(::parse) ?: fallback
    }

    private fun fromBuildConfig(): PrimarySource {
        val configured = BuildConfig.IPTV_ORG_URL.trim()
        return if (configured.equals("disabled", ignoreCase = true)) {
            PrimarySource(false, "Desactivada", "")
        } else PrimarySource(configured.isNotBlank(), "Fuente principal", configured)
    }

    private fun parse(json: String): PrimarySource? = runCatching {
        val root = JsonParser.parseString(json).asJsonObject
        val source = root.getAsJsonObject("fuentePrincipal")
            ?: root.getAsJsonObject("primarySource")
            ?: throw IllegalArgumentException("Falta fuentePrincipal")
        val enabled = (source.get("habilitada") ?: source.get("enabled"))
            ?.takeIf { !it.isJsonNull }?.asBoolean ?: true
        val name = (source.get("nombre") ?: source.get("name"))
            ?.takeIf { !it.isJsonNull }?.asString?.trim().orEmpty().ifBlank { "Fuente remota" }
        val url = (source.get("url") ?: source.get("playlistUrl"))
            ?.takeIf { !it.isJsonNull }?.asString?.trim().orEmpty()
        if (enabled && !url.startsWith("https://", ignoreCase = true)) {
            throw IllegalArgumentException("La fuente activa debe usar HTTPS")
        }
        PrimarySource(enabled && url.isNotBlank(), name, if (enabled) url else "")
    }.onFailure {
        Log.w(TAG, "No se pudo interpretar la configuración (${it.javaClass.simpleName})")
    }.getOrNull()

    private fun download(address: String): String {
        require(address.startsWith("https://", ignoreCase = true)) { "La URL de configuración debe usar HTTPS" }
        val connection = URL(address).openConnection() as HttpURLConnection
        return try {
            connection.connectTimeout = CONNECT_TIMEOUT_MS
            connection.readTimeout = READ_TIMEOUT_MS
            connection.requestMethod = "GET"
            connection.setRequestProperty("Accept", "application/json")
            connection.setRequestProperty("Cache-Control", "no-cache")
            val status = connection.responseCode
            if (status !in 200..299) throw IllegalStateException("HTTP $status")
            connection.inputStream.bufferedReader(Charsets.UTF_8).use { it.readText() }
        } finally {
            connection.disconnect()
        }
    }
}
