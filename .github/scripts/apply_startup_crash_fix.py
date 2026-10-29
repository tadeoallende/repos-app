#!/usr/bin/env python3
"""Apply the user's startup-crash fix to the verified extracted AngulismoTV project."""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Uso: apply_startup_crash_fix.py PROJECT_DIR")

root = Path(sys.argv[1]).resolve()
repository = root / "app/src/main/java/com/angulismotv/data/ChannelRepository.kt"
reporter = root / "app/src/main/java/com/angulismotv/utils/CrashReporter.kt"
proguard = root / "app/proguard-rules.pro"

for path in (repository, reporter, proguard):
    if not path.is_file():
        raise SystemExit(f"Falta archivo requerido: {path}")

# Avoid TypeToken anonymous subclasses whose generic signature can be rewritten by R8.
text = repository.read_text(encoding="utf-8")
old = "private val cacheType = object : TypeToken<List<Channel>>() {}.type"
new = "private val cacheType = TypeToken.getParameterized(List::class.java, Channel::class.java).type"
if old in text:
    text = text.replace(old, new, 1)
elif new not in text:
    raise SystemExit("No se encontró el ancla cacheType esperada; no se aplicó el parche.")
repository.write_text(text, encoding="utf-8")

# Keep the Gson generic-token API and its type metadata available in minified Release builds.
rules = proguard.read_text(encoding="utf-8")
required_rules = [
    "-keep,allowobfuscation,allowshrinking class com.google.gson.reflect.TypeToken",
    "-keep,allowobfuscation,allowshrinking class * extends com.google.gson.reflect.TypeToken",
]
for rule in required_rules:
    if rule not in rules:
        rules = rules.rstrip() + "\n" + rule + "\n"
proguard.write_text(rules, encoding="utf-8")

# Temporarily enable the in-app stack trace screen in Release for diagnosis of startup crashes.
report = reporter.read_text(encoding="utf-8")
guard = "        if (!BuildConfig.DEBUG) return"
if guard in report:
    report = report.replace(
        guard,
        "        // TEMPORAL: habilitado también en Release para diagnosticar cierres al iniciar.\n"
        "        // Al cerrar la investigación, restaurar: if (!BuildConfig.DEBUG) return",
        1,
    )
elif "TEMPORAL: habilitado también en Release" not in report:
    raise SystemExit("No se encontró el guard esperado de CrashReporter; no se aplicó el parche.")
reporter.write_text(report, encoding="utf-8")

assert new in repository.read_text(encoding="utf-8")
assert all(rule in proguard.read_text(encoding="utf-8") for rule in required_rules)
assert "TEMPORAL: habilitado también en Release" in reporter.read_text(encoding="utf-8")
print("Corrección de arranque aplicada: Gson TypeToken + reglas R8 + CrashReporter temporal en Release.")
