#!/usr/bin/env bash
set -Eeuo pipefail

APK="${1:?Uso: test-release-startup.sh APK APP_ID PREFIX}"
APP_ID="${2:?Falta el identificador de la aplicación}"
NAME="${3:?Falta el prefijo de diagnóstico}"
WORKSPACE="${GITHUB_WORKSPACE:?GITHUB_WORKSPACE no está definido}"
PREFIX="$WORKSPACE/$NAME"
mkdir -p "$WORKSPACE"

fail() {
  echo "::error::$1"
  for file in "${PREFIX}-device.txt" "${PREFIX}-install.txt" "${PREFIX}-start.txt" "${PREFIX}-logcat.txt"; do
    if [[ -s "$file" ]]; then
      echo "----- $file -----"
      tail -n 180 "$file" || true
    fi
  done
  exit 1
}

if [[ ! -s "$APK" ]]; then fail "No se encontró el APK para la prueba de arranque: $APK"; fi

# Wait for ADB to recover if the emulator temporarily reports offline.
# Hosted runners without KVM can take a long time to boot; retry the bridge
# without treating a temporarily-offline emulator as an app crash.
adb start-server >/dev/null 2>&1 || true
DEVICE_STATE=""
for attempt in $(seq 1 60); do
  DEVICE_STATE="$(adb get-state 2>/dev/null || true)"
  if [[ "$DEVICE_STATE" == "device" ]]; then break; fi
  if (( attempt % 10 == 0 )); then
    adb reconnect offline >/dev/null 2>&1 || true
    adb start-server >/dev/null 2>&1 || true
  fi
  sleep 2
done
adb devices -l > "${PREFIX}-device.txt" 2>&1 || true
if [[ "$DEVICE_STATE" != "device" ]]; then
  fail "El emulador no quedó disponible por ADB (estado: ${DEVICE_STATE:-desconocido}); no se atribuye a un crash de la app."
fi

if ! timeout 120s adb install -r "$APK" > "${PREFIX}-install.txt" 2>&1; then
  fail "No se pudo instalar el APK en el emulador; revisar el log de instalación."
fi

adb logcat -c
adb shell am force-stop "$APP_ID" >/dev/null 2>&1 || true
START_RC=0
timeout 45s adb shell am start -W -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -p "$APP_ID" > "${PREFIX}-start.txt" 2>&1 || START_RC=$?
sleep 12
adb logcat -d -v threadtime > "${PREFIX}-logcat.txt" 2>&1 || true
adb shell dumpsys activity activities > "${PREFIX}-activities.txt" 2>&1 || true
adb exec-out screencap -p > "${PREFIX}-screen.png" 2>/dev/null || true
PID="$(adb shell pidof "$APP_ID" 2>/dev/null | tr -d '\r' | xargs || true)"

if [[ "$START_RC" -ne 0 || -z "$PID" ]] || grep -Eq 'FATAL EXCEPTION|Fatal signal [0-9]+|Process: com\.angulismotv|>>> com\.angulismotv <<<' "${PREFIX}-logcat.txt"; then
  fail "AngulismoTV no superó la prueba de inicio en $NAME; comprobar logcat y salida de am start."
fi

echo "Inicio verificado para $APP_ID con PID $PID; diagnóstico guardado bajo $PREFIX-*"
