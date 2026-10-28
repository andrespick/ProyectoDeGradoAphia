# Hyperdrive

Hyperdrive mantiene un pool de conexiones hacia MySQL y entrega al Worker los parámetros de
conexión en el binding `HYPERDRIVE` (`host`, `port`, `user`, `password`, `database`), que
`integrations/cloudflare.py` convierte en `DatabaseConfig`.

Fuente: https://developers.cloudflare.com/hyperdrive/examples/python-workers/
(requiere `compatibility_date` ≥ 2026-09-08; controlador recomendado para MySQL: `aiomysql`).

## Crear la configuración (producción)

Requiere el servicio VPC de MySQL ([túnel](tunnel-y-acceso-privado.md)):

```bash
pnpm --filter @aphia/api exec wrangler hyperdrive create aphia-production \
  --service-id <VPC_SERVICE_ID_MYSQL> \
  --database aphia \
  --user aphia_app \
  --password "$(cat /ruta/segura/mysql_app_password)" \
  --scheme mysql
```

Copie el `id` devuelto en `apps/api/wrangler.jsonc` → `env.production.hyperdrive[0].id`.
Repita para staging con su propia base, usuario y `id`.

El id no es secreto, pero no invente ni reutilice ids: cada entorno tiene el suyo.

## Desarrollo local

`pywrangler dev` usa la variable `CLOUDFLARE_HYPERDRIVE_LOCAL_CONNECTION_STRING_HYPERDRIVE`,
que `scripts/run.mjs` construye desde `.env`
(`mysql://aphia_app:…@127.0.0.1:3307/aphia`). En este modo **no hay pool ni caché**: el
Worker conecta directo a MySQL. El id de Hyperdrive local es un marcador (ceros).

## Consideraciones

- El Worker abre una conexión por operación y la cierra; el pool real lo mantiene Hyperdrive.
- Hyperdrive puede almacenar en caché consultas de lectura. Si una pantalla necesita datos
  estrictamente actuales, revise la configuración de caché de la configuración de Hyperdrive.
- Si cambia la contraseña de `aphia_app`, actualice Hyperdrive:
  `wrangler hyperdrive update <ID> --password ...`.
