# APHIA

Aplicación web interna para **APHIA S.A.S.**, inmobiliaria ubicada en Colombia. Administrará
clientes, propietarios, inmuebles, contratos, documentos, usuarios, permisos y trazabilidad.

> **Estado actual (v0.1.0):** las siete fases del [plan de implementación](docs/plan-de-implementacion.md) están hechas:
> inicio de sesión real (usuario y contraseña, bloqueo configurable, sesiones revocables), usuarios y roles,
> clientes, propietarios y codeudores sobre el [modelo 3FN](docs/arquitectura/modelo-de-datos.md)
> (una persona puede tener varios papeles), inmuebles con propietarios y servicios públicos,
> contratos con partes, filtros e impresión, búsqueda global, tablero, identidad visual, ayuda en
> línea (`/ayuda`), [manual de usuario](docs/manual-usuario.md), respaldo local cifrado,
> administración del sistema (estado y respaldos, auditoría, catálogos, política de seguridad,
> datos de la empresa, clave temporal y papelera) y
> [guía de instalación y mantenimiento](docs/despliegue/instalacion-y-mantenimiento.md).

## Arquitectura en una línea

React + Vite en **Cloudflare Pages** → FastAPI en **Cloudflare Python Workers** →
**Hyperdrive** + **Cloudflare Tunnel / Workers VPC** → **MySQL 8.4** y servicio de documentos en
un **VPS Linux** con Docker. La misma API corre también con **Uvicorn** en cualquier Linux.

Detalle y diagramas: [docs/arquitectura](docs/arquitectura/README.md).

## Tecnologías

| Capa | Tecnología | Versión verificada |
| --- | --- | --- |
| Frontend | React · React Router · TypeScript · Vite | 19.3 · 8.5 · 7.0 · 8.3 |
| Pruebas frontend | Vitest · Testing Library · Playwright | 5.0 · 16.3 · 1.64 |
| API | Python · FastAPI · Pydantic · aiomysql | 3.13 local / 3.14 en Workers · 0.162 · 2.14 · 0.3.2 |
| Runtime API | Cloudflare Python Workers (pywrangler · wrangler) | 1.17.9 · 4.153 |
| Runtime alternativo | Uvicorn (ASGI) | 0.54 |
| Base de datos | MySQL LTS | 8.4.13 |
| Documentos | FastAPI + volumen Docker | — |
| Herramientas | pnpm · uv · Node.js · Docker Compose | 12.15 · 0.13.6 · 24 · v5 |
| Calidad | Ruff · Pytest · HTTPX | 0.17 · 9.2 · 0.28 |

Las versiones exactas quedan fijadas en `pnpm-lock.yaml`, `apps/api/uv.lock`,
`apps/api/pylock.toml` (paquete del Worker) y `apps/files/uv.lock`.

## Requisitos previos

- **Node.js 22.12+** (probado con 24) y **pnpm 12** (`corepack enable` o instalación de pnpm).
- **uv** ([instalación](https://docs.astral.sh/uv/getting-started/installation/)). uv descarga
  Python 3.13 si no está instalado.
- **Docker Desktop** (Windows/macOS) o **Docker Engine + Compose** (Linux), en ejecución.
- Git. No se necesita cuenta de Cloudflare ni VPS para desarrollar.

## Instalación

```bash
git clone https://github.com/andrespick/ProyectoDeGradoAphia.git
cd ProyectoDeGradoAphia
pnpm install          # dependencias JS (incluye wrangler y Playwright)
pnpm env:init         # crea .env y apps/api/.dev.vars con secretos locales aleatorios
pnpm infra:up         # MySQL 8.4 y servicio de documentos en Docker
pnpm db:migrate       # aplica migraciones
pnpm db:seed          # carga catálogos y datos ficticios
pnpm dev              # frontend + API (Python Workers local)
```

Las dependencias de Python se instalan solas con `uv run` la primera vez. Usuarios de
desarrollo (los crea `pnpm db:seed`; contraseña `Aphia.2026`, solo para development/test):

| Usuario | Rol |
| --- | --- |
| `admin` | Administrador de Sistemas (gestiona usuarios) |
| `administrativo` | Administrativo (crea, edita y elimina) |
| `asesor` | Asesor (crea y edita, no elimina) |

| Servicio | URL local |
| --- | --- |
| Frontend | http://localhost:5173 |
| API | http://localhost:8787 (documentación: http://localhost:8787/api/docs) |
| MySQL | 127.0.0.1:3307 |
| MySQL de pruebas | 127.0.0.1:3308 (solo durante `pnpm test:integration`) |
| Servicio de documentos | 127.0.0.1:4000 |

## Comandos

| Comando | Qué hace |
| --- | --- |
| `pnpm dev` | Crea `.env` y `apps/api/.dev.vars` si faltan, levanta Docker y ejecuta web + API en Python Workers local con recarga |
| `pnpm dev:asgi` | Igual, pero la API corre con Uvicorn (ruta de ejecución Linux tradicional) |
| `pnpm infra:up` / `pnpm infra:down` | Inicia / detiene MySQL y documentos (los datos se conservan) |
| `pnpm infra:logs` · `pnpm infra:ps` | Registros y estado de los contenedores |
| `pnpm infra:reset -- --yes` | **Borra** los volúmenes locales (MySQL y documentos) |
| `pnpm db:migrate` · `pnpm db:status` | Aplica / consulta migraciones |
| `pnpm db:seed` | Carga datos ficticios (solo development/test) |
| `pnpm lint` · `pnpm typecheck` | Ruff (Python) y TypeScript |
| `pnpm test` | Pruebas unitarias: web (Vitest), API y documentos (Pytest). No requiere Docker |
| `pnpm test:integration` | API ↔ MySQL real y servicio de documentos en Docker |
| `pnpm test:e2e` | Playwright de extremo a extremo (primera vez: `pnpm test:e2e:install`) |
| `pnpm build` | Compila el frontend en `apps/web/dist` |
| `pnpm check:worker` | Empaqueta el Worker sin desplegar (`pywrangler deploy --dry-run`) |

## Pruebas

```bash
pnpm test               # 217 pruebas unitarias (50 web + 136 API + 31 documentos)
pnpm test:integration   # 37 API↔MySQL (personas, login, usuarios, catálogos, modelo 3FN, migraciones) + 5 documentos en Docker
pnpm test:e2e           # 21 escenarios en Chromium (+ smoke en Firefox y WebKit) contra el stack completo
```

Estrategia y cobertura: [docs/pruebas](docs/pruebas/README.md).

## Variables de entorno

El archivo `.env` de la raíz (creado por `pnpm env:init` desde [.env.example](.env.example))
alimenta Docker Compose, los scripts y la API local. **Nunca se versiona.**

| Variable | Uso |
| --- | --- |
| `MYSQL_ROOT_PASSWORD`, `DB_PASSWORD` | Contraseñas locales de MySQL (generadas) |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` | Conexión local (Uvicorn, migraciones y Hyperdrive local) |
| `TEST_DB_*` | MySQL de pruebas de integración |
| `FILES_SERVICE_TOKEN` | Token entre servicios para el servicio de documentos (generado) |
| `FILES_MAX_BYTES`, `FILES_ALLOWED_TYPES` | Límites de archivos |
| `AUTH_SECRET` | Clave de firma de los tokens de sesión (generada; `pnpm env:init` la copia también a `apps/api/.dev.vars` para el Worker local) |
| `CORS_ORIGINS`, `AUTH_MODE`, `LOG_LEVEL`, `APP_ENV` | API con Uvicorn (`pnpm dev:asgi`). `AUTH_MODE=database` es el modo real |

Con Python Workers, las variables no secretas de cada entorno están en
[apps/api/wrangler.jsonc](apps/api/wrangler.jsonc) y los secretos se cargan con
`wrangler secret put`. El frontend solo usa `VITE_API_BASE_URL` (pública).

## Estructura

```text
apps/web      Frontend React + Vite (Cloudflare Pages)
apps/api      API FastAPI (Cloudflare Python Workers / Uvicorn)
apps/files    Servicio privado de documentos (Docker en el VPS)
database      Migraciones SQL versionadas (modelo 3FN), datos ficticios y scripts
infra         Docker Compose local y de producción, túnel, respaldos
tests         Pruebas de integración entre servicios y E2E (Playwright)
docs          Requisitos, arquitectura, desarrollo, despliegue, seguridad y pruebas
scripts       Utilidades Node multiplataforma (dev, infra, entorno)
```

Responsabilidades de cada carpeta y reglas de trabajo: [docs/desarrollo](docs/desarrollo/README.md).

## Solución de problemas

| Síntoma | Solución |
| --- | --- |
| `No se encontró "docker"` o `infra:up` falla | Inicie Docker Desktop y espere a que diga *Engine running*. En una terminal nueva, `docker version` debe mostrar el servidor. |
| `uv` o `docker` no se reconocen tras instalarlos | Abra una terminal nueva (el PATH se actualiza al iniciar sesión). |
| Puerto 3307, 4000, 5173 u 8787 en uso | Cambie `DB_PORT`/`FILES_PORT` en `.env`, o cierre el proceso que lo ocupa (`netstat -ano \| findstr :8787`). |
| La primera solicitud a la API tarda ~10 s | Normal en `pywrangler dev`: carga Pyodide la primera vez. Las siguientes tardan milisegundos. |
| `UnicodeDecodeError: 'charmap'` al ejecutar pywrangler en Windows | Use los scripts de pnpm (definen `PYTHONUTF8=1`) o defina esa variable en su terminal. |
| `/api/ready` responde `not_ready` | MySQL no está arriba o faltan migraciones: `pnpm infra:up && pnpm db:migrate`. |
| El login responde «Usuario o contraseña incorrectos» con `admin` | Falta cargar los usuarios de desarrollo: `pnpm db:seed`. |
| La API responde 500 `configuracion_invalida` al arrancar | Falta `AUTH_SECRET` (≥ 32 caracteres): `pnpm env:init` lo genera en `.env` y `apps/api/.dev.vars`. |
| `pnpm install` avisa de *build scripts* ignorados | Ya están aprobados en `pnpm-workspace.yaml` (`allowBuilds`); si agrega otro, use `pnpm approve-builds`. |
| `test:e2e` falla con «Executable doesn't exist» | Instale los navegadores: `pnpm test:e2e:install` (Chromium, Firefox y WebKit). |
| En Pages la web muestra el gestor sin pedir usuario y sin datos | Se construyó sin `VITE_API_BASE_URL`: defínala en Pages con la URL del Worker y redespliegue (ver [cloudflare-pages.md](docs/despliegue/cloudflare-pages.md)). |
| Cambié la contraseña en `.env` y MySQL rechaza la conexión | MySQL solo usa las variables al crear el volumen. `pnpm infra:reset -- --yes` (borra datos locales) y repita la instalación. |

## Documentación

- [Plan de implementación](docs/plan-de-implementacion.md) (fases, criterios de aceptación y estado)
- [Requisitos y alcance](docs/requisitos/README.md)
- [Identidad visual](docs/diseno/README.md)
- [Arquitectura](docs/arquitectura/README.md) y [modelo de datos](docs/arquitectura/modelo-de-datos.md)
- [Desarrollo](docs/desarrollo/README.md)
- [Pruebas](docs/pruebas/README.md)
- [Seguridad](docs/seguridad/README.md)
- [Despliegue](docs/despliegue/README.md)

## Autor

- Andrés Felipe Vela Flórez
