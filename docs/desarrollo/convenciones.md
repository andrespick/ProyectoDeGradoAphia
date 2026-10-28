# Convenciones de código

## General

- Idioma del dominio, mensajes y documentación: español. Identificadores técnicos pueden ir en inglés.
- Cambios pequeños y enfocados; sin abstracciones que no resuelvan un problema actual.
- Nada de secretos ni datos personales reales en el repositorio.
- Finales de línea LF (`.gitattributes`).

## Python (API y documentos)

- Python 3.13, `from __future__ import annotations`, tipado completo.
- Formato y lint: `pnpm lint` (Ruff, longitud 100, reglas `E,F,W,I,B,UP,S,BLE,SIM,RUF,ASYNC`).
- Dependencias FastAPI con `Annotated`. Esquemas Pydantic con `extra="forbid"` en entradas.
- Errores: subclases de `core.errors.AppError` con `status_code`, `code` (snake_case en
  español) y `default_message`. Nunca devolver trazas ni SQL.
- SQL siempre parametrizado (`%s`). Fechas en UTC (`DATETIME(6)`; la sesión usa `+00:00`).
- Logging con `core.logging.log_event(logger, nivel, "evento", campo=valor)`; sin datos personales.
- Pruebas: `test_<comportamiento>` descriptivo en español; patrón preparar/actuar/verificar.

## TypeScript / React

- Modo estricto, sin `any`. `verbatimModuleSyntax`: use `import type` para tipos.
- Componentes funcionales; estado de datos en hooks (`useX`) dentro de `features/`.
- Accesibilidad: `label` asociado a cada campo, `role="alert"` para errores, `role="status"`
  para estados, `aria-invalid` en campos con error.
- HTTP solo a través de `services/apiClient.ts` (timeout, errores normalizados, sin cookies).
- Pruebas por comportamiento visible (Testing Library: roles y textos, no clases CSS).

## API REST

- Prefijo `/api/v1/<recurso>` (plural, español). Salud: `/api/health`, `/api/ready`.
- `GET` lista con `limit` (1–100) y `offset`; respuesta `{items, total, limit, offset}`.
- `POST` crea → 201 con el recurso. Validación → 422. Duplicados → 409. Sin sesión → 401.
  Sin rol → 403. Dependencia caída → 503.
- Errores: `{"error": {"codigo", "mensaje", "request_id", "detalles?"}}`; cabecera `X-Request-ID`.

## Git

- Ramas cortas desde `main`; mensajes de commit en imperativo describiendo el porqué.
- La CI debe pasar antes de integrar.
