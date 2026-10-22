# AngulismoTV — Etapa 39: catálogo americano y canales propios

## Comportamiento

- La fuente oficial IPTV-org se consulta usando index.m3u para conservar metadatos de categoría y país.
- De esa fuente se mantienen los canales con país identificado en América (América del Norte, América Central, América del Sur y el Caribe).
- También se conservan canales de la categoría internacional y una lista conservadora de cadenas internacionales reconocidas, aunque su país de origen esté fuera de América.
- Si un canal de IPTV-org no tiene país identificable ni coincide con una cadena internacional reconocida, se excluye en vez de asumir su región.
- Una URL M3U personalizada configurada como IPTV_ORG_URL se conserva sin filtro regional.
- La fuente CUSTOM_CHANNELS_URL se carga siempre en paralelo y se combina con el catálogo oficial. Esta fuente personal no está limitada geográficamente.
- CHANNELS_URL y EVENTS_URL mantienen su comportamiento de respaldo para instalaciones existentes.

## Cómo agregar canales propios sin volver a compilar

La app usa por defecto este archivo público del repositorio:
https://raw.githubusercontent.com/tadeoallende/repos-app/main/canales.json

Se puede editar canales.json desde GitHub con la opción Edit. Los cambios se leen cuando la app vuelve a cargar o actualizar el catálogo; no hace falta subir otro APK solo para cambiar esa lista. El archivo tiene que permanecer como JSON válido.

Formato de ejemplo:

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
        },
        {
          "name": "Canal con reproductor web",
          "category": "Entretenimiento",
          "options": [
            {
              "name": "Web",
              "iframe": "https://ejemplo.com/player",
              "streamType": "iframe"
            }
          ]
        }
      ]
    }

Campos principales:

- name: obligatorio.
- streamUrl: URL HTTP/HTTPS directa, por ejemplo HLS (.m3u8); puede omitirse si el canal usa options.
- options: fuentes alternativas web opcionales; cada una usa iframe con su URL y streamType, normalmente iframe.
- logo, category y country: opcionales.
- show: false permite ocultar una entrada sin borrarla.

Importante: la fuente personal se agrega a los canales oficiales, no los reemplaza. Solo agregá URLs que tengas autorización para usar. Un enlace puede estar caído o dejar de funcionar, y la app no puede garantizar la disponibilidad de la transmisión.

## Verificación

Se añadieron pruebas unitarias para países americanos, cadenas internacionales, países ajenos a América y fuentes M3U personalizadas. La compilación debe comprobarse en GitHub Actions; no se considera validada hasta que la ejecución termine correctamente.
