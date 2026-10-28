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
pnpm dev            # Docker + web (5173) + API en Python Workers local (8787)
# … editar código: Vite y pywrangler recargan automáticamente
pnpm lint && pnpm typecheck && pnpm test
pnpm infra:down     # al terminar (los datos se conservan)
```

`pnpm dev:asgi` ejecuta la API con Uvicorn en lugar de Workers. Úselo para depurar con
herramientas de Python estándar, pero valide siempre los cambios también con `pnpm dev`,
que reproduce el runtime de producción.

## Diferencias entre desarrollo local y producción

| Aspecto | Local | Producción |
| --- | --- | --- |
| Runtime de la API | workerd local (`pywrangler dev`) | Cloudflare Workers |
| Conexión a MySQL | Hyperdrive con cadena local: conexión directa, **sin pool ni caché** | Hyperdrive con pool, vía Workers VPC y túnel |
| TLS a MySQL | No | Sí (obligatorio) |
| Variables | `wrangler.jsonc` (`vars` raíz) + `.env` | `env.staging` / `env.production` + secretos |
| Autenticación | Usuario ficticio | Cerrada hasta implementar la real |
| Servicio de documentos | `127.0.0.1:4000` (Docker) | Red interna del VPS, solo vía túnel |
