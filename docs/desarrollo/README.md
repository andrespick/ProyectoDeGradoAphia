# Desarrollo

- [Cómo crear un módulo](crear-modulo.md)
- [Convenciones de código](convenciones.md)
- [Migraciones](migraciones.md)
- [Docker en desarrollo](docker.md)
- [Cómo ejecutar pruebas](../pruebas/README.md)

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
| `database/migrations` | Migraciones SQL versionadas `NNNN_descripcion.sql` (`0001` demo; `0002`–`0007` modelo 3FN) |
| `database/seeds` | Datos ficticios idempotentes |
| `database/scripts` | `migrate.py`, `seed.py` |
| `infra/local` · `infra/production` | Compose local · Compose del VPS, túnel, respaldos |
| `tests/integration` · `tests/e2e` | Pruebas entre servicios · Playwright |
| `scripts` | Utilidades Node multiplataforma usadas por `pnpm` |
| `docs` | Documentación del proyecto (en español) |

## Flujo diario

```bash
pnpm dev            # Docker + web (5173) + API con Uvicorn (8000)
# … editar código: Vite y Uvicorn (--reload) recargan automáticamente
pnpm lint && pnpm typecheck && pnpm test
pnpm infra:down     # al terminar (los datos se conservan)
```

## Diferencias entre desarrollo local y producción

| Aspecto | Local | Producción |
| --- | --- | --- |
| API | Uvicorn con recarga en `127.0.0.1:8000` | Uvicorn en Docker (`127.0.0.1:8000`) detrás de Caddy (HTTPS) |
| Conexión a MySQL | Directa a `127.0.0.1:3307` | Red interna `backend` de Docker |
| TLS a MySQL | No | Sí (obligatorio) |
| Variables | `.env` de la raíz | `infra/production/.env.production` + Docker secrets (`*_FILE`) |
| Autenticación | Login real con los usuarios de `pnpm db:seed` (`AUTH_SECRET` en `.env`) | Login real (`AUTH_SECRET` en `secrets/auth_secret`) |
| Servicio de documentos | `127.0.0.1:4000` (Docker) | Red interna `backend`, solo lo alcanza la API |
