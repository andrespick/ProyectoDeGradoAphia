# Cómo crear un módulo

Ejemplo: módulo `propietarios`. El módulo de referencia es `apps/api/src/modules/clientes`.

## 1. Migración

Cree `database/migrations/0002_crear_propietarios.sql` (ver [migraciones](migraciones.md)) y
aplíquela con `pnpm db:migrate`. Si necesita datos de ejemplo, agregue un archivo idempotente
en `database/seeds/` (solo datos ficticios).

## 2. Backend (`apps/api/src/modules/propietarios/`)

| Archivo | Responsabilidad |
| --- | --- |
| `schemas.py` | Modelos Pydantic de entrada (`extra="forbid"`, longitudes, validadores) y salida |
| `repository.py` | SQL parametrizado con `Database.connection()` / `Database.transaction()`; traduce errores de MySQL a errores de dominio |
| `service.py` | Reglas de negocio; depende de un `Protocol` del repositorio; errores heredan de `core.errors` |
| `router.py` | `APIRouter(prefix="/api/v1/propietarios")`, dependencia de roles, inyección del servicio |

Registre el router en `src/main.py` (`app.include_router(...)`).

Reglas:

- Cada endpoint protegido declara roles: `dependencies=[Depends(require_roles(Role.ADMIN, ...))]`.
- Use `Annotated[..., Depends(...)]` y `Query(ge=..., le=...)` para paginación acotada.
- Escrituras dentro de `async with db.transaction() as conn`.
- No importe `integrations.cloudflare` ni `workers` desde el módulo.

## 3. Pruebas del backend

- `tests/unit/test_propietarios.py`: reemplace el repositorio con `app.dependency_overrides`
  (ver `InMemoryClientesRepository` en `tests/conftest.py`). Cubra éxito, validación (422),
  conflictos (409), permisos (401/403).
- `tests/integration/test_propietarios_mysql.py` con `pytestmark = [pytest.mark.integration, ...]`
  para verificar SQL real. Limpie sus tablas en un fixture como hace `db_conn`.

## 4. Frontend (`apps/web/src/`)

1. Tipos en `types/propietario.ts`.
2. Servicio en `services/propietariosService.ts` usando `apiRequest`.
3. Feature en `features/propietarios/` (hook de datos, formulario, tabla, validación).
4. Página en `pages/` y ruta en `routes/routes.tsx` (dentro de `ProtectedRoute` con roles).
5. Pruebas con Vitest + Testing Library usando `test/mockApi.ts`.

## 5. Verificación y documentación

```bash
pnpm lint && pnpm typecheck && pnpm test && pnpm test:integration && pnpm test:e2e
```

Actualice `docs/` si el módulo introduce variables, dependencias o decisiones nuevas.
