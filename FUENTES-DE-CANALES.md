# Cambiar la fuente principal de canales desde GitHub

AngulismoTV consulta la configuración remota en `fuentes.json`. Así podés activar, desactivar o reemplazar la fuente principal sin compilar otra APK cada vez. La app necesita una compilación que ya incluya la función de configuración remota.

## Dónde editarla

- En producción: [fuentes.json en main](https://github.com/tadeoallende/repos-app/blob/main/fuentes.json)
- Para probar: [fuentes.json en la rama de prueba](https://github.com/tadeoallende/repos-app/blob/chatgpt/prueba-acceso-2026-10-21-3/fuentes.json)

Editá el archivo en la rama que usa la app que querés configurar. El workflow de compilación apunta a `fuentes.json` de la misma rama que se está probando; así una prueba en la rama de trabajo no hereda el interruptor de producción.

## Mantener IPTV-org

```json
{
  "version": 1,
  "fuentePrincipal": {
    "habilitada": true,
    "nombre": "IPTV-org",
    "url": "https://iptv-org.github.io/iptv/index.m3u"
  }
}
```

## Desactivar IPTV-org

```json
{
  "version": 1,
  "fuentePrincipal": {
    "habilitada": false,
    "nombre": "Desactivada",
    "url": ""
  }
}
```

La app deja de consultar esa fuente y pasa al catálogo personal; si este tampoco tiene canales válidos, prueba las fuentes heredadas que estén configuradas.

## Usar otro proveedor

Reemplazá el nombre y la URL. La URL debe ser HTTPS y apuntar directamente a una playlist M3U compatible, no a una página HTML de GitHub ni a un archivo JSON.

```json
{
  "version": 1,
  "fuentePrincipal": {
    "habilitada": true,
    "nombre": "Mi proveedor",
    "url": "https://raw.githubusercontent.com/USUARIO/REPOSITORIO/RAMA/playlist.m3u"
  }
}
```

Reemplazá los segmentos de ejemplo por la ruta real de la lista. Las URLs oficiales de IPTV-org se reconocen y pasan por la política regional existente; las playlists personalizadas no reciben ese filtro regional.

## Cuándo se aplica

La app obtiene esta configuración cuando carga o vuelve a cargar el catálogo de canales. No hace falta recompilar después de cada edición de `fuentes.json`. Si GitHub no responde o el JSON nuevo es inválido, la app usa la última configuración válida guardada localmente; si no hay una caché previa, utiliza la configuración incluida al compilar.

## Fuentes complementarias y de respaldo

- `CUSTOM_CHANNELS_URL`: catálogo personal, normalmente `canales.json`.
- `CHANNELS_URL`: fuente adicional de canales compatible con el lector del proyecto.
- `EVENTS_URL`: fuente adicional de eventos/canales deportivos.

La prioridad es exclusiva: fuente principal; si no produce canales válidos, catálogo personal; si tampoco está disponible, fuente heredada de canales y, por último, eventos deportivos. La app no concatena el catálogo personal a una fuente principal que ya funciona.
