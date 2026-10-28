# Instrucciones para agentes de programación (APHIA)

Lea este archivo antes de modificar el repositorio. Aplica a cualquier agente o asistente
automatizado y también sirve como guía rápida para personas.

## Arquitectura

- **Frontend** (`apps/web`): React 19 + TypeScript + Vite, desplegado en Cloudflare Pages.
  Consume la API REST por HTTPS usando `VITE_API_BASE_URL`.
- **API** (`apps/api`): FastAPI. Destino principal: **Cloudflare Python Workers** (Pyodide).
  Ruta alternativa obligatoria: **Uvicorn** en Linux. `src/main.py` es ASGI puro;
  `src/entry.py` es el único archivo que importa el paquete `workers`.
- **Base de datos**: MySQL 8.4. En Workers se accede con **aiomysql vía Hyperdrive**; con Uvicorn,
  con aiomysql directo. Una conexión por operación (`db/connection.py`).
- **Documentos** (`apps/files`): servicio FastAPI privado en el VPS con volumen persistente.
  Solo lo invoca la API con un token de servicio. Nunca se expone a usuarios finales.
- **Conectividad de producción**: Cloudflare Tunnel + Workers VPC (beta) + Hyperdrive. MySQL y el
  servicio de documentos no publican puertos.

Documento completo: `docs/arquitectura/README.md`.

## Responsabilidad de cada carpeta

| Carpeta | Contenido |
| --- | --- |
| `apps/web/src/components` | Componentes visuales reutilizables sin lógica de negocio |
| `apps/web/src/features/<dominio>` | Componentes, hooks y validaciones de un dominio |
| `apps/web/src/services` | Acceso HTTP a la API (`apiClient.ts` es el único que llama a `fetch`) |
| `apps/web/src/routes`, `layouts`, `pages`, `hooks`, `types` | Ruteo, estructura, pantallas, hooks compartidos, tipos |
| `apps/api/src/core` | Configuración, errores, logging, middleware (transversal) |
| `apps/api/src/db` | Configuración y conexiones MySQL |
| `apps/api/src/integrations` | Adaptadores de plataforma (Cloudflare). La lógica de negocio no los importa |
| `apps/api/src/modules/<dominio>` | `router.py`, `service.py`, `repository.py`, `schemas.py` |
| `apps/files/src` | Servicio de documentos (`storage.py` concentra el acceso a disco) |
| `database/migrations` | Migraciones SQL versionadas `NNNN_descripcion.sql` |
| `database/seeds` | Datos ficticios idempotentes |
| `database/scripts` | `migrate.py`, `seed.py` |
| `infra/local` · `infra/production` | Compose local · Compose del VPS, túnel, respaldos |
| `tests/integration` · `tests/e2e` | Pruebas entre servicios · Playwright |
| `scripts` | Utilidades Node multiplataforma usadas por `pnpm` |
| `docs` | Documentación del proyecto (en español) |

## Convenciones

- Idioma: dominio, mensajes al usuario y documentación en **español**; código de
  infraestructura e identificadores técnicos pueden ir en inglés. Mantenga el estilo vecino.
- Python: 3.13, Ruff (`pnpm lint`), tipado completo, `from __future__ import annotations`.
  Dependencias FastAPI con `Annotated[...]`. Errores de negocio heredan de `core.errors.AppError`.
- SQL: **siempre parametrizado** (`%s`). Nunca f-strings ni concatenación con datos.
- TypeScript: modo estricto; sin `any`. Las llamadas HTTP pasan por `services/`.
- Respuestas de error de la API: `{"error": {"codigo", "mensaje", "request_id", "detalles?"}}`.
- Nada de capas o patrones adicionales sin una necesidad concreta.

## Compatibilidad con Python Workers

- Antes de agregar una dependencia a `apps/api/pyproject.toml` (`[project].dependencies`),
  verifique que funcione en Pyodide (paquete puro o con wheel Pyodide) y ejecútela con
  `pnpm --filter @aphia/api dev`. Las herramientas de desarrollo van en `[dependency-groups]`.
- No abra sockets ni conexiones en el ámbito global del módulo; solo dentro de una solicitud.
- No use SQLAlchemy asíncrono (requiere greenlet, no soportado).
- No lea `os.environ` para configuración en Workers: use `core.runtime.get_settings(request)`.

## Requisitos de pruebas

- Todo cambio de comportamiento incluye pruebas. Antes de terminar ejecute:
  `pnpm lint && pnpm typecheck && pnpm test`; si toca SQL o documentos, también
  `pnpm test:integration`; si toca el flujo de pantalla, `pnpm test:e2e`.
- No marque como superada una prueba que no se ejecutó. Informe los fallos con su salida.
- Use solo datos ficticios (dominios `example.test`/`example.com`). Nunca datos personales reales.

## Restricciones de seguridad

- **Prohibido introducir secretos** en archivos versionados: contraseñas, tokens, cadenas de
  conexión, claves privadas, IDs de cuentas reales. Use `.env` (local), `wrangler secret put`,
  GitHub Secrets o `infra/production/secrets/` (no versionado).
- No inventar identificadores de recursos de Cloudflare: use los marcadores `REEMPLAZAR_*`.
- No publicar puertos de MySQL ni del servicio de documentos fuera de `127.0.0.1` (local) o de la
  red interna de Docker (producción).
- CORS solo con orígenes explícitos; nunca `*`.
- `AUTH_MODE=development` es exclusivo de development/test. No presentar ese modo como
  autenticación real. La autenticación de producción está pendiente.
- No registrar en logs cuerpos de solicitudes, query strings, tokens ni datos personales.
- No ejecutar despliegues, migraciones de producción ni cambios en recursos externos sin
  autorización explícita de una persona.

## Reglas para migraciones

- Una migración aplicada **no se edita**: cree `NNNN+1_descripcion.sql` (el checksum lo detecta).
- Preferir una sentencia DDL por migración (MySQL confirma implícitamente cada DDL).
- Sentencias terminadas en `;` al final de línea; sin `DELIMITER` ni procedimientos.
- Cambios destructivos (DROP, cambios de tipo) en dos pasos: compatibilidad primero, limpieza después.
- En producción: respaldo verificado antes de migrar y `--confirm-backup`. Nunca al iniciar el Worker.
- Pruebe con `pnpm db:migrate` y `pnpm test:integration`.

## Documentación

Actualice la documentación en el mismo cambio cuando modifique: arquitectura, comandos,
variables de entorno, puertos, dependencias relevantes, procesos de despliegue o seguridad.
Como mínimo revise `README.md`, `AGENTS.md` y el documento de `docs/` afectado.
