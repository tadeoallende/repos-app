# Configurar el respaldo IPTV-org de AngulismoTV

El catálogo personal de `canales.json` es siempre la fuente principal. `fuentes.json` controla el respaldo IPTV-org, que solo se consulta si el catálogo personal falla o no entrega canales válidos. La app necesita una compilación que ya incluya la función de configuración remota.

## Dónde editarlo

- En producción: [fuentes.json en main](https://github.com/tadeoallende/repos-app/blob/main/fuentes.json)
- Para probar: [fuentes.json en la rama de prueba](https://github.com/tadeoallende/repos-app/blob/chatgpt/prueba-acceso-2026-10-21-3/fuentes.json)

Editá el archivo de la rama que usa la app que querés configurar. El workflow de compilación apunta a la configuración de la misma rama, así la prueba no hereda el interruptor de producción.

## Habilitar IPTV-org como respaldo

El archivo de prueba conserva el nombre de campo heredado `fuentePrincipal` por compatibilidad; la app lo utiliza como proveedor alternativo después de probar el catálogo personal.

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

Desactivarlo no afecta el catálogo personal: `canales.json` sigue siendo la fuente principal. Si esa lista tampoco entrega canales válidos, se prueban las fuentes heredadas configuradas.

## Usar otro proveedor como respaldo

Reemplazá el nombre y la URL. La URL debe ser HTTPS y apuntar directamente a una playlist M3U compatible.

La prioridad es fija y exclusiva: `canales.json`; IPTV-org; `CHANNELS_URL`; `EVENTS_URL`. Las listas no se concatenan.
