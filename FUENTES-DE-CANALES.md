# Configurar la fuente principal de canales (IPTV-org)

La URL de la fuente principal se puede cambiar desde la configuración del repositorio en GitHub. No hace falta modificar Kotlin ni editar el ZIP manualmente; sí hay que generar una nueva APK para que el cambio llegue a los usuarios.

## Dónde configurarla

1. Abrí el repositorio en GitHub.
2. Entrá en **Settings → Secrets and variables → Actions → Variables**.
3. Creá o editá la variable de repositorio `IPTV_ORG_URL`.

La variable `vars.IPTV_ORG_URL` tiene prioridad sobre el secreto heredado `IPTV_ORG_URL`. Si no hay ninguno configurado, la compilación usa la URL oficial de IPTV-org por defecto.

## Opciones de valor

### Mantener IPTV-org

```text
https://iptv-org.github.io/iptv/index.m3u
```

### Desactivarlo

```text
disabled
```

Se acepta `disabled` sin distinguir mayúsculas/minúsculas. Al desactivar esta fuente, AngulismoTV sigue cargando el catálogo personal (`CUSTOM_CHANNELS_URL`) y, si están configurados, los respaldos `CHANNELS_URL` y `EVENTS_URL`. Desactivar IPTV-org no desactiva esas otras fuentes.

### Cambiarlo por otra lista

Poné la URL HTTPS de una playlist M3U compatible, por ejemplo, una playlist publicada en otro repositorio de GitHub:

```text
https://raw.githubusercontent.com/USUARIO/REPOSITORIO/RAMA/playlist.m3u
```

Reemplazá los segmentos de ejemplo por la ubicación real de tu archivo. La URL debe devolver el contenido M3U directamente, no la página HTML de GitHub ni un JSON. Las URLs oficiales de IPTV-org siguen pasando por su normalización y filtro regional; una fuente M3U personalizada se carga sin ese filtro específico.

## Después de cambiarla

Guardá la variable y ejecutá **Actions → Build desde ZIP → Run workflow** sobre la rama que quieras compilar. La dirección se incluye en la configuración de compilación de la APK: el cambio afecta las APK nuevas, no las ya instaladas. Para probarlo, revisá los resultados de la compilación antes de distribuirla.

## Otras fuentes

- `CUSTOM_CHANNELS_URL`: catálogo personal, normalmente `canales.json` del repositorio.
- `CHANNELS_URL`: fuente JSON/M3U de respaldo compatible con el lector del proyecto.
- `EVENTS_URL`: fuente de eventos/canales deportivos de respaldo.

Estas fuentes son independientes de `IPTV_ORG_URL`.
