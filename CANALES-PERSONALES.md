# AngulismoTV — catálogo personal de canales

La app combina automáticamente la lista pública de IPTV-org filtrada para América con el catálogo personal guardado en este archivo: canales.json.

## Agregar o quitar canales

1. Abrí el archivo canales.json en el repositorio de GitHub.
2. Elegí Edit (el lápiz).
3. Dentro del arreglo "channels", agregá un objeto por canal respetando la coma entre objetos.
4. Guardá los cambios con Commit changes. La app consultará la lista cuando vuelva a cargar el catálogo; no hace falta compilar otro APK para cambiar estos datos.

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

Para una fuente con reproductor web se puede omitir streamUrl y añadir options:

    "options": [
      {
        "name": "Web",
        "iframe": "https://ejemplo.com/player",
        "streamType": "iframe"
      }
    ]

name es obligatorio. streamType admite hls, dash, mp4, auto o iframe. logo, category y country son opcionales. Usá show: false para ocultar temporalmente un canal sin eliminarlo. La lista personal no se filtra por país, a diferencia de la fuente pública principal.

El archivo debe ser JSON válido: sin comentarios, sin comas finales y con comillas dobles. Usá únicamente URLs que tengas autorización para distribuir. La disponibilidad y la estabilidad de cada transmisión dependen de su proveedor.
