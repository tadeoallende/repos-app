# AngulismoTV — catálogo personal de canales

El archivo `canales.json` es el **respaldo** de la fuente principal configurada en `fuentes.json`.

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

1. La app usa la fuente principal configurada en `fuentes.json` si descarga canales válidos.
2. Si la principal está desactivada, falla o no produce canales válidos, usa este catálogo personal.
3. Solo si también falta o falla `canales.json`, prueba las fuentes heredadas `CHANNELS_URL` y `EVENTS_URL`, en ese orden.

**Los catálogos no se mezclan:** una fuente de respaldo reemplaza a la anterior, no se concatena con una fuente principal que ya funciona. Así se evita duplicar canales y alterar la identidad o numeración del catálogo activo.

El archivo debe ser JSON válido: sin comentarios, sin comas finales y con comillas dobles. Usá únicamente URLs que tengas autorización para distribuir. La disponibilidad y estabilidad de cada transmisión dependen de su proveedor.
