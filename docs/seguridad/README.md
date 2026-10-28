# Seguridad

## Controles implementados

| Control | Dónde | Verificado |
| --- | --- | --- |
| Secretos fuera del repositorio (`.env`, `.dev.vars`, `secrets/`, `backup.env` ignorados) | `.gitignore` | ✅ |
| Contraseñas locales aleatorias generadas por `pnpm env:init` | `scripts/env-init.mjs` | ✅ |
| Validación de entradas con Pydantic (`extra="forbid"`, longitudes, formato) | `modules/*/schemas.py` | ✅ |
| SQL parametrizado; usuario de la app sin permisos DDL | repositorios, `01-usuarios.sh` | ✅ |
| CORS con orígenes explícitos; `*` rechazado al cargar la configuración | `core/config.py`, `core/middleware.py` | ✅ |
| Cabeceras: CSP `default-src 'none'`, `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy`, `Cache-Control: no-store`, HSTS fuera de local | `core/middleware.py`, `apps/web/public/_headers` | ✅ |
| Errores centralizados sin trazas, SQL ni eco de valores enviados; `request_id` para soporte | `core/errors.py` | ✅ |
| Logs JSON sin cuerpos, query strings, tokens ni credenciales | `core/logging.py` | ✅ |
| Documentación OpenAPI solo en development/test | `core/docs.py` | ✅ |
| Autenticación propia: usuario y contraseña, PBKDF2-SHA256 con sal por usuario (100 000 iteraciones), token HMAC-SHA256 de 8 h, bloqueo 3 intentos → 15 min | `modules/auth` | ✅ |
| Roles `admin_sistemas` / `administrativo` / `asesor` en todos los routers (`require_roles` con grupos); solo `admin_sistemas` gestiona usuarios; el último administrador activo no se puede eliminar ni degradar | `modules/auth`, `modules/usuarios` | ✅ |
| Servicio de documentos: token de servicio (comparación en tiempo constante), tipo por firma, tamaño máximo, ids UUID, sin *path traversal*, sin sobrescritura, contenedor sin privilegios y de solo lectura | `apps/files` | ✅ |
| MySQL y documentos sin puertos públicos; red interna sin salida a Internet; TLS obligatorio a MySQL | `infra/production/compose.yaml`, `aphia.cnf` | ✅ (en réplica local) |
| Bases separadas por entorno (desarrollo, pruebas, staging, producción) | Compose, Hyperdrive por entorno | Parcial (staging/prod por crear) |
| Despliegue a producción solo con aprobación y desde `main` | `.github/workflows/deploy.yml` | Configurado, no ejecutado |
| Respaldos cifrados con `age` fuera del VPS | `infra/production/backup` | Comandos de volcado verificados; ciclo completo no ejecutado |

## Autenticación

`AUTH_MODE=database` (local, staging y producción): los usuarios viven en `user_account` /
`user_role` y entran con usuario y contraseña en `POST /api/v1/auth/login`.

| Aspecto | Implementación |
| --- | --- |
| Contraseñas | PBKDF2-HMAC-SHA256, sal aleatoria de 16 bytes por usuario, 100 000 iteraciones; formato `pbkdf2_sha256$iter$sal$hash` (`modules/auth/passwords.py`). En Pyodide (Workers) no existe `hashlib.pbkdf2_hmac`, así que se usa una implementación pura equivalente (probada contra `hashlib`). Medido en el Worker local: ~260 ms por inicio de sesión; cabe en el plan de pago de Workers (30 s de CPU) pero no en el gratuito (10 ms): en ese caso la API debe servirse con Uvicorn. |
| Sesión | Token `base64url(JSON{sub, nombre, roles, exp}).firma` con HMAC-SHA256 y `AUTH_SECRET` (≥ 32 caracteres, nunca versionado); vigencia 8 h; se envía como `Authorization: Bearer`. Sin estado en el servidor: desactivar un usuario o cambiar su rol aplica en el siguiente inicio de sesión o al vencer el token; rotar `AUTH_SECRET` cierra todas las sesiones. La web lo guarda en `sessionStorage` (o `localStorage` con «Recordarme»). |
| Bloqueo | 3 intentos fallidos consecutivos → `locked_until = ahora + 15 min` (`register_failed_attempt` con `SELECT … FOR UPDATE`); el login correcto reinicia el contador; una cuenta bloqueada responde 423 aunque la clave sea correcta. El evento `cuenta_bloqueada` queda en los logs y la pantalla de Usuarios muestra la cuenta con «Desbloquear» (`POST /api/v1/usuarios/{id}/desbloquear`). |
| Enumeración de usuarios | Usuario inexistente, inactivo o clave incorrecta responden el mismo 401 `credenciales_invalidas`; los inexistentes verifican contra un hash ficticio para igualar el tiempo. |
| Logs | Nunca incluyen usuario, clave ni token; solo `account_id` e intentos. |
| Desarrollo | `AUTH_MODE=development` (usuario ficticio) queda **solo** para pruebas unitarias; `pnpm env:init` genera `AUTH_SECRET` en `.env` y `apps/api/.dev.vars`, y `pnpm db:seed` crea `admin`, `administrativo` y `asesor` con la contraseña `Aphia.2026` (nunca en staging/producción). |

Primer administrador en producción: ver `docs/despliegue/instalacion-y-mantenimiento.md`
(se escribe en la fase 5; mientras tanto, genere el hash con `hash_password` y ejecute los
`INSERT` de `person`, `person_document`, `user_account` y `user_role` como en
`database/seeds/0003_usuarios_desarrollo.sql`).

## Manejo de secretos

| Secreto | Desarrollo | Producción |
| --- | --- | --- |
| Contraseñas MySQL | `.env` (generado) | `infra/production/secrets/` en el VPS (generate-secrets.sh) |
| Contraseña `aphia_app` para Hyperdrive | — | Configuración de Hyperdrive (Cloudflare) |
| Token del servicio de documentos | `.env` | `secrets/files_service_token` + `wrangler secret put FILES_SERVICE_TOKEN` |
| `AUTH_SECRET` (firma de tokens de sesión) | `.env` y `apps/api/.dev.vars` (generados) | `wrangler secret put AUTH_SECRET --env …`; con Uvicorn, variable de entorno |
| Token del túnel | — | `infra/production/.env.production` (chmod 600) |
| Token de API de Cloudflare | — | GitHub Environment secrets |
| Clave privada `age` de respaldos | — | **Fuera del VPS** (gestor de contraseñas) |

Rotación: cambie el valor en el origen (secreto Docker / Hyperdrive / Worker), reinicie el
servicio afectado y verifique `/api/ready`. Rote inmediatamente ante cualquier sospecha de fuga.

## Datos personales

- Desarrollo y pruebas usan exclusivamente datos ficticios (`example.test`).
- Antes de cargar datos reales, definir con la empresa la política de tratamiento de datos
  (Ley 1581 de 2012) y los permisos de acceso por rol.

## Pendientes de seguridad

- Auditoría de acciones e intentos de acceso (bitácora con actor y fecha).
- Límite de tasa (Cloudflare WAF / Rate Limiting) en la API.
- Endurecimiento del VPS (ver `docs/despliegue/vps.md`) y monitoreo de logs.
- Integración API ↔ documentos con autorización por entidad (quién puede ver qué contrato).
- Escaneo de dependencias en CI (p. ej. Dependabot) y revisión periódica de versiones.
