# GitHub Actions

## CI (`.github/workflows/ci.yml`)

Se ejecuta en cada push a `main` y en cada pull request. No usa secretos.

| Job | Contenido |
| --- | --- |
| `web` | `pnpm install --frozen-lockfile`, TypeScript, Vitest, build |
| `api` | `uv sync --frozen`, Ruff (lint y formato), Pytest unitarias, Pytest integración con servicio `mysql:8.4` |
| `files` | Ruff, Pytest, `docker build` del servicio de documentos y de la API |
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
| Secret | `VPS_SSH_HOST` | IP o nombre del VPS |
| Secret | `VPS_SSH_USER` | Usuario con acceso a Docker (`aphia`) |
| Secret | `VPS_SSH_KEY` | Clave privada OpenSSH de despliegue (ver abajo) |
| Secret | `VPS_SSH_KNOWN_HOSTS` | Salida de `ssh-keyscan <host>` (fija la huella del servidor) |
| Secret | `CLOUDFLARE_API_TOKEN` | Token con permiso *Cloudflare Pages: Edit* |
| Secret | `CLOUDFLARE_ACCOUNT_ID` | Id de la cuenta |
| Variable | `CLOUDFLARE_PAGES_PROJECT` | Nombre del proyecto de Pages |
| Variable | `API_BASE_URL` | URL pública de la API (Caddy), por ejemplo `https://api.aphia.example.com` |
| Variable | `VPS_DEPLOY_PATH` | Opcional; ruta del clon en el VPS (`/opt/aphia`) |

Si falta cualquiera, el job falla antes de desplegar.

### Clave SSH de despliegue

En el VPS, como `aphia`: `ssh-keygen -t ed25519 -f ~/.ssh/github_deploy -N ""`, agregue
`github_deploy.pub` a `~/.ssh/authorized_keys`, copie la clave privada al secreto
`VPS_SSH_KEY` y borre el archivo privado del servidor. El job ejecuta por SSH
`git fetch` + `git checkout <commit>` en `VPS_DEPLOY_PATH` y
`docker compose up -d --build api files`; MySQL no se reinicia y las migraciones siguen
siendo manuales.

## Primera ejecución

Los workflows están escritos pero **no se han ejecutado en GitHub**. Tras el primer push revise
la pestaña Actions; las versiones mayores de las acciones (`actions/checkout@v5`,
`actions/setup-node@v5`, `pnpm/action-setup@v4`, `astral-sh/setup-uv@v6`) pueden actualizarse.
