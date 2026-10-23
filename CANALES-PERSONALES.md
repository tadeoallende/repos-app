# AngulismoTV — catálogo personal de canales

El archivo `canales.json` es la **fuente principal** de AngulismoTV. La aplicación respeta la lista que mantenés ahí como catálogo autoritativo.

## Agregar o quitar canales

1. Abrí `canales.json` en GitHub.
2. Elegí Edit (el lápiz).
3. Dentro del arreglo `"channels"`, agregá un objeto por canal respetando las comas entre objetos.
4. Guardá los cambios con Commit changes. La app consultará la lista al volver a cargar el catálogo; no hace falta compilar otra APK para actualizarla.

Ejemplo para un canal directo:

    {
      "channels": [
        {
          "name": "Mi canal",
          "logo": "https://ejemplo.com/logo.png",
          "streamUrl": "https://ejemplo.com/en-vivo/index.m3u8",
          "streamType": "hls",
          "category": "Deportes",
          "country": "ar",
          "show": true
        }
      ]
    }

Para una fuente con reproductor web se puede omitir `streamUrl` y añadir `options`:

    "options": [
      {
        "name": "Web",
        "iframe": "https://ejemplo.com/player",
        "streamType": "iframe"
      }
    ]

`name` es obligatorio. `streamType` admite `hls`, `dash`, `mp4`, `auto` o `iframe`. `logo`, `category` y `country` son opcionales. Usá `show: false` para ocultar temporalmente un canal sin eliminarlo. El catálogo personal no se filtra por país.

## Orden de selección

1. **Principal:** el catálogo personal configurado en `CUSTOM_CHANNELS_URL` (normalmente este `canales.json`).
2. **Respaldo:** IPTV-org, si la lista personal falla, está vacía o no tiene canales válidos. Su configuración está en `fuentes.json`.
3. **Último recurso:** las fuentes heredadas `CHANNELS_URL` y `EVENTS_URL`, en ese orden.

**Las listas no se mezclan.** Cuando una fuente tiene datos válidos, se utiliza esa lista sola; una fuente de respaldo nunca se concatena a la principal. Esto evita introducir canales que no mantenés, duplicados y cambios inesperados en la identidad o numeración.

El archivo debe ser JSON válido: sin comentarios, sin comas finales y con comillas dobles. Usá únicamente URLs que tengas autorización para distribuir. La disponibilidad y estabilidad de cada transmisión dependen de su proveedor.
