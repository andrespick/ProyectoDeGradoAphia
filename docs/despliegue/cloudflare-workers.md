# Cloudflare Workers (API)

Configuración: `apps/api/wrangler.jsonc`. Herramientas: `pywrangler` (paquete `workers-py`,
vía `uv run`) y `wrangler` (dependencia de `apps/api`).

## Entornos

| Entorno | Worker | Comando |
| --- | --- | --- |
| Local | `aphia-api-local` (nunca se despliega) | `pnpm --filter @aphia/api dev` |
| Staging | `aphia-api-staging` | `pnpm --filter @aphia/api deploy:staging` |
| Producción | `aphia-api` | `pnpm --filter @aphia/api deploy:production` |

Antes del primer despliegue reemplace en `wrangler.jsonc` todos los `REEMPLAZAR_*`:
ids de Hyperdrive, ids de servicios VPC y el origen de Pages en `CORS_ORIGINS`. El workflow
de despliegue se detiene si quedan marcadores.

## Validar sin desplegar

```bash
pnpm check:worker
# equivale a: cd apps/api && uv run pywrangler deploy --dry-run --outdir dist
```

Resultado actual: 9,8 MB sin comprimir, 2,45 MB gzip.

## Secretos

```bash
cd apps/api
uv run pywrangler login
uv run pywrangler secret put FILES_SERVICE_TOKEN --env production
```

Las variables no secretas (`APP_ENV`, `CORS_ORIGINS`, `AUTH_MODE`, `LOG_LEVEL`) van en `vars`
de cada entorno. `AUTH_MODE` debe ser `disabled` fuera de local.

## Despliegue

Preferentemente con el workflow `Deploy` de GitHub Actions ([github-actions.md](github-actions.md)).
Manual (requiere `CLOUDFLARE_API_TOKEN` y `CLOUDFLARE_ACCOUNT_ID` o `wrangler login`):

```bash
cd apps/api
uv run pywrangler deploy --env staging
```

`pywrangler deploy` ejecuta `sync` (instala dependencias Pyodide en `src/vendor`) y luego
`wrangler deploy`.

## Verificación posterior

```bash
curl https://<worker>/api/health   # runtime "workers", environment correcto
curl https://<worker>/api/ready    # database "ok"
```

Logs: `uv run pywrangler tail --env production` o el panel (observability habilitado).

## Reversión

```bash
uv run pywrangler deployments list --env production
uv run pywrangler rollback --env production
```

Una reversión del Worker no revierte migraciones: por eso las migraciones deben ser compatibles
con la versión anterior de la API (ver migraciones en dos fases).
