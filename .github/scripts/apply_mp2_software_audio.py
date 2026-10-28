#!/usr/bin/env python3
"""Enable ExoPlayer's FFmpeg audio extension as a software fallback.

The overlay is deliberately idempotent: CI can safely reapply it to a clean ZIP.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
version_catalog = root / "gradle/libs.versions.toml"
player_factory = root / "app/src/main/java/com/angulismotv/player/StreamMediaSourceFactory.kt"
proguard = root / "app/proguard-rules.pro"

for required in (version_catalog, player_factory, proguard):
    if not required.is_file():
        raise SystemExit(f"ERROR: falta el archivo de proyecto esperado: {required}")

# Pin the extension version alongside ExoPlayer 2.19.1.
versions = version_catalog.read_text(encoding="utf-8")
if 'ffmpegExtension = "1.0.0"' not in versions:
    needle = 'exoplayer = "2.19.1"\n'
    if needle not in versions:
        raise SystemExit("ERROR: no se encontró la versión ExoPlayer esperada en libs.versions.toml")
    versions = versions.replace(needle, needle + 'ffmpegExtension = "1.0.0"\n', 1)

library_decl = 'exoplayer-ffmpeg = { module = "io.github.shenbengit.exoplayer-extensions:ffmpeg", version.ref = "ffmpegExtension" }'
if library_decl not in versions:
    needle = 'exoplayer-okhttp = { module = "com.google.android.exoplayer:extension-okhttp", version.ref = "exoplayer" }\n'
    if needle not in versions:
        raise SystemExit("ERROR: no se encontró el bloque de bibliotecas ExoPlayer esperado")
    versions = versions.replace(needle, needle + library_decl + '\n', 1)

bundle_old = 'media-playback = ["exoplayer-core", "exoplayer-hls", "exoplayer-dash", "exoplayer-ui", "exoplayer-okhttp"]'
bundle_new = 'media-playback = ["exoplayer-core", "exoplayer-hls", "exoplayer-dash", "exoplayer-ui", "exoplayer-okhttp", "exoplayer-ffmpeg"]'
if bundle_new not in versions:
    if bundle_old not in versions:
        raise SystemExit("ERROR: no se encontró el bundle media-playback esperado")
    versions = versions.replace(bundle_old, bundle_new, 1)
version_catalog.write_text(versions, encoding="utf-8")

# Enable the extension only as a fallback, keeping Android platform decoders first.
source = player_factory.read_text(encoding="utf-8")
old_factory = '''    /**
     * Si el decodificador preferido de un códec no se puede inicializar, ExoPlayer prueba
     * los demás decodificadores del dispositivo antes de descartar la pista. No agrega códecs
     * nuevos: solo evita perder audio por un decodificador defectuoso. Lo usan ambos reproductores.
     */
    fun createRenderersFactory(context: Context): DefaultRenderersFactory =
        DefaultRenderersFactory(context).setEnableDecoderFallback(true)
'''
new_factory = '''    /**
     * Conserva los decodificadores de Android como primera opción y habilita FFmpeg como
     * fallback por software para formatos de audio que el dispositivo no pueda decodificar.
     * Incluye MPEG Layer I/II/III (MP1/MP2/MP3), además de otros formatos de audio.
     * Se comparte entre mini-player y pantalla completa para evitar comportamientos distintos.
     */
    fun createRenderersFactory(context: Context): DefaultRenderersFactory =
        DefaultRenderersFactory(context)
            .setEnableDecoderFallback(true)
            .setExtensionRendererMode(DefaultRenderersFactory.EXTENSION_RENDERER_MODE_ON)
'''
if new_factory not in source:
    if old_factory not in source:
        raise SystemExit("ERROR: no se encontró la implementación esperada de createRenderersFactory")
    source = source.replace(old_factory, new_factory, 1)
player_factory.write_text(source, encoding="utf-8")

# Keep reflection-loaded renderer classes from being stripped by R8.
rules = proguard.read_text(encoding="utf-8")
proguard_rule = '-keep class com.google.android.exoplayer2.ext.ffmpeg.** { *; }'
if proguard_rule not in rules:
    proguard.write_text(
        rules.rstrip()
        + "\n\n# Renderer FFmpeg de ExoPlayer: se carga por reflexión desde DefaultRenderersFactory.\n"
        + proguard_rule + "\n",
        encoding="utf-8",
    )

# Validate the overlay before Gradle resolves the native dependency.
versions = version_catalog.read_text(encoding="utf-8")
source = player_factory.read_text(encoding="utf-8")
rules = proguard.read_text(encoding="utf-8")
assert library_decl in versions and bundle_new in versions
assert 'setExtensionRendererMode(DefaultRenderersFactory.EXTENSION_RENDERER_MODE_ON)' in source
assert 'setEnableDecoderFallback(true)' in source
assert proguard_rule in rules
print("MP2 software-audio fallback enabled: ExoPlayer platform-first + FFmpeg extension (MP1/MP2/MP3).")
