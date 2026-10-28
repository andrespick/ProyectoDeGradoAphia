# GitHub Actions

## CI (`.github/workflows/ci.yml`)

Se ejecuta en cada push a `main` y en cada pull request. No usa secretos.

| Job | Contenido |
| --- | --- |
| `web` | `pnpm install --frozen-lockfile`, TypeScript, Vitest, build |
| `api` | `uv sync --frozen`, Ruff (lint y formato), Pytest unitarias, Pytest integración con servicio `mysql:8.4` |
| `files` | Ruff, Pytest, `docker build` |
| `worker` | `pywrangler deploy --dry-run` para local, staging y producción |
| `e2e` | MySQL de servicio, migraciones, Playwright con la API en Python Workers local |

Las credenciales de MySQL de CI son efímeras y solo existen en el contenedor del job.

## Deploy (`.github/workflows/deploy.yml`)

Manual (Actions → Deploy → Run workflow → elegir entorno). Ejecuta primero toda la CI.
Producción solo desde `main`. **No ejecuta migraciones.**

### Configuración necesaria

1. Settings → Environments → crear `staging` y `production`.
2. En `production`: **Required reviewers** (al menos una persona) y restringir a la rama `main`.
3. En cada entorno:

| Tipo | Nombre | Valor |
| --- | --- | --- |
| Secret | `CLOUDFLARE_API_TOKEN` | Token con permisos mínimos: *Workers Scripts: Edit*, *Cloudflare Pages: Edit*, *Hyperdrive: Read* (ajuste según la cuenta) |
| Secret | `CLOUDFLARE_ACCOUNT_ID` | Id de la cuenta |
| Variable | `CLOUDFLARE_PAGES_PROJECT` | Nombre del proyecto de Pages |
| Variable | `API_BASE_URL` | URL pública del Worker del entorno |

Si falta cualquiera, el job falla antes de desplegar.

## Primera ejecución

Los workflows están escritos pero **no se han ejecutado en GitHub**. Tras el primer push revise
la pestaña Actions; las versiones mayores de las acciones (`actions/checkout@v5`,
`actions/setup-node@v5`, `pnpm/action-setup@v4`, `astral-sh/setup-uv@v6`) pueden actualizarse.
