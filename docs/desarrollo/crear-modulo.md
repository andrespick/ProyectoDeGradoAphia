# Cómo crear un módulo

Ejemplo: módulo `propietarios`. El módulo de referencia es `apps/api/src/modules/clientes`.

## 1. Tablas

Las tablas del negocio ya existen (migraciones `0002`–`0007`, ver
[modelo de datos](../arquitectura/modelo-de-datos.md)). Para propietarios se usan `person`,
`person_document`, `person_phone`, `person_email` y el vínculo `property_owner`.

Solo si el módulo necesita un cambio de esquema, cree una migración nueva (`0011_...`, ver
[migraciones](migraciones.md)) y aplíquela con `pnpm db:migrate`. Si necesita datos de ejemplo,
agregue un archivo idempotente en `database/seeds/` (solo datos ficticios).

Los nombres de tablas y columnas están en inglés (modelo 3FN); los esquemas Pydantic y la API
usan español. La traducción entre ambos ocurre en `repository.py`.

## 2. Backend (`apps/api/src/modules/propietarios/`)

| Archivo | Responsabilidad |
| --- | --- |
| `schemas.py` | Modelos Pydantic de entrada (`extra="forbid"`, longitudes, validadores) y salida |
| `repository.py` | SQL parametrizado con `Database.connection()` / `Database.transaction()`; traduce errores de MySQL a errores de dominio |
| `service.py` | Reglas de negocio; depende de un `Protocol` del repositorio; errores heredan de `core.errors` |
| `router.py` | `APIRouter(prefix="/api/v1/propietarios")`, dependencia de roles, inyección del servicio |

Registre el router en `src/main.py` (`app.include_router(...)`).

Reglas:

- Cada endpoint protegido declara roles con los grupos de `modules/auth/schemas.py`: el router
  completo con `dependencies=[Depends(require_roles(*LECTURA))]` y cada `DELETE` con
  `require_roles(*ELIMINACION)`; solo `/api/v1/usuarios` usa `GESTION_USUARIOS`.
- Errores de MySQL: use `db.sql.mysql_error_code(exc)` con `ER_DUP_ENTRY` (1062, duplicado →
  409), `ER_ROW_IS_REFERENCED` (1451, borrado con referencias → 409) y `ER_NO_REFERENCED_ROW`
  (1452, FK inexistente → 404). Filtros de texto con `db.sql.like_pattern` y
  `COLLATE utf8mb4_0900_ai_ci` cuando no deban distinguir mayúsculas ni acentos.
- Códigos de catálogo: insértelos con `INSERT … SELECT … FROM <catalogo> WHERE code = %s` y
  trate `rowcount == 0` como código inválido, en vez de fijarlos con `Literal`.
- Use `Annotated[..., Depends(...)]` y `Query(ge=..., le=...)` para paginación acotada.
- Escrituras dentro de `async with db.transaction() as conn`.
- No importe `integrations.cloudflare` ni `workers` desde el módulo.

## 3. Pruebas del backend

- `tests/unit/test_propietarios.py`: reemplace el repositorio con `app.dependency_overrides`
  (los repositorios en memoria viven en `tests/fakes.py`; regístrelos en la fixture `app` de
  `tests/conftest.py`). Cubra éxito, validación (422), conflictos (409), permisos (401/403).
- `tests/integration/test_propietarios_mysql.py` con `pytestmark = [pytest.mark.integration, ...]`
  para verificar SQL real. Limpie sus tablas en un fixture como hace `db_conn`.

## 4. Frontend (`apps/web/src/`)

1. Tipos en `types/propietario.ts`.
2. Servicio en `services/propietariosService.ts` usando `apiRequest`.
3. Feature en `features/propietarios/` (hook de datos, formulario, tabla, validación).
4. Página en `pages/` y ruta en `routes/routes.tsx` (dentro de `ProtectedRoute` con roles).
5. Pruebas con Vitest + Testing Library usando `test/mockApi.ts` (fixture `CATALOGOS`).

Reutilice los componentes compartidos (`components/Field`, `SelectField`, `TextAreaField`,
`Pagination`, `Segmented`, `KpiCard`, `Avatar`, `SlideOver`), `hooks/usePagedList` para los
listados con filtros en la URL, `features/catalogos/useCatalogos` para los selects y
`features/shared/validation.ts` para traducir los 422. Siga la plantilla de página y las
insignias descritas en `docs/diseno/README.md`.

## 5. Verificación y documentación

```bash
pnpm lint && pnpm typecheck && pnpm test && pnpm test:integration && pnpm test:e2e
```

Actualice `docs/` si el módulo introduce variables, dependencias o decisiones nuevas.
