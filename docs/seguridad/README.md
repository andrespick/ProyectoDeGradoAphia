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
| Autenticación propia: usuario y contraseña, PBKDF2-SHA256 con sal por usuario (100 000 iteraciones), token HMAC-SHA256, bloqueo tras intentos fallidos; intentos, minutos, vigencia de la sesión y largo mínimo de la clave según la política configurable (3 / 15 min / 8 h / 8 por defecto) | `modules/auth`, `modules/configuracion` | ✅ |
| Sesiones revocables: cada solicitud compara la `session_version` del token con la de MySQL (cerrar sesiones, restablecer o cambiar la clave, cambiar el rol o desactivar la cuenta surten efecto de inmediato) | `modules/auth/dependencies.py` | ✅ |
| Clave temporal generada por el sistema (12+ caracteres, se muestra una sola vez); con ella solo se puede cambiar la contraseña (403 `cambio_de_clave_requerido`) | `modules/usuarios`, `modules/auth` | ✅ |
| Roles `admin_sistemas` / `administrativo` / `asesor` en todos los routers (`require_roles` con grupos); solo `admin_sistemas` gestiona el sistema (usuarios, auditoría, catálogos, configuración, papelera, respaldos) y no accede a los módulos de negocio; el último administrador activo no se puede eliminar ni degradar | `modules/auth`, `modules/usuarios` | ✅ |
| Auditoría: inicios de sesión exitosos, intentos fallidos de cuentas existentes y bloqueos, y toda escritura desde la API, con actor, fecha y `request_id`; sin contraseñas, tokens ni datos de formularios. Los intentos contra cuentas inexistentes o inactivas y los que llegan con la cuenta bloqueada van solo a los logs: así un anónimo no puede escribir filas sin límite (el bloqueo acota lo que sí se audita) | `modules/auditoria`, tabla `audit_event` | ✅ |
| Papelera: instantánea del registro eliminado guardada en la misma transacción; solo `admin_sistemas` la consulta, restaura o vacía | `modules/papelera`, tabla `deleted_record` | ✅ |
| Servicio de documentos: token de servicio (comparación en tiempo constante), tipo por firma, tamaño máximo, ids UUID, sin *path traversal*, sin sobrescritura, contenedor sin privilegios y de solo lectura | `apps/files` | ✅ |
| MySQL y documentos sin puertos públicos; red interna sin salida a Internet; TLS obligatorio a MySQL | `infra/production/compose.yaml`, `aphia.cnf` | ✅ (en réplica local) |
| Bases separadas por entorno (desarrollo, pruebas, staging, producción) | Compose, Hyperdrive por entorno | Parcial (staging/prod por crear) |
| Despliegue a producción solo con aprobación y desde `main` | `.github/workflows/deploy.yml` | Configurado, no ejecutado |
| Respaldos cifrados con `age`: copia local diaria (directorio 700, archivos 600, retención) y copia externa opcional; cada ejecución queda en `backup_run` y se ve en Sistema. La API no ejecuta comandos en el VPS: solo anota solicitudes que `backup.sh --solicitudes` atiende | `infra/production/backup`, `modules/sistema` | Comandos de volcado y SQL de registro verificados; ciclo completo no ejecutado en un VPS real |
| Código de soporte (`request_id`) en cada error mostrado al usuario, sin exponer trazas | `apiClient.errorMessage` | ✅ |

## Autenticación

`AUTH_MODE=database` (local, staging y producción): los usuarios viven en `user_account` /
`user_role` y entran con usuario y contraseña en `POST /api/v1/auth/login`.

| Aspecto | Implementación |
| --- | --- |
| Contraseñas | PBKDF2-HMAC-SHA256, sal aleatoria de 16 bytes por usuario, 100 000 iteraciones; formato `pbkdf2_sha256$iter$sal$hash` (`modules/auth/passwords.py`). En Pyodide (Workers) no existe `hashlib.pbkdf2_hmac`, así que se usa una implementación pura equivalente (probada contra `hashlib`). Medido en el Worker local: ~260 ms por inicio de sesión; cabe en el plan de pago de Workers (30 s de CPU) pero no en el gratuito (10 ms): en ese caso la API debe servirse con Uvicorn. |
| Sesión | Token `base64url(JSON{sub, nombre, roles, exp, ver}).firma` con HMAC-SHA256 y `AUTH_SECRET` (≥ 32 caracteres, nunca versionado); vigencia según la política (8 h por defecto); se envía como `Authorization: Bearer`. `ver` es la `session_version` de la cuenta: cada solicitud la compara con MySQL (una consulta por clave primaria), así que desactivar la cuenta, cambiar su rol o su clave, restablecerla o «Cerrar sesiones» invalidan los tokens de inmediato. Rotar `AUTH_SECRET` cierra todas las sesiones. La web lo guarda en `sessionStorage` (o `localStorage` con «Recordarme»). |
| Cambio de contraseña | `POST /api/v1/auth/cambiar-clave` exige la clave actual, una nueva distinta que cumpla la política, incrementa `session_version` (cierra las demás sesiones) y entrega un token nuevo. Tras un restablecimiento (`must_change_password = 1`) `require_roles` responde 403 `cambio_de_clave_requerido` a todo salvo `/auth/me` y `/auth/cambiar-clave`. |
| Bloqueo | `max_intentos` fallidos consecutivos (3 por defecto) → `locked_until = ahora + minutos_bloqueo` (15 por defecto) con `register_failed_attempt` (`SELECT … FOR UPDATE`); el login correcto reinicia el contador; una cuenta bloqueada responde 423 aunque la clave sea correcta. El evento queda en los logs (`cuenta_bloqueada`), en la auditoría y en la pantalla de Usuarios con «Desbloquear». Los valores se cambian en Configuración dentro de los límites de los CHECK de `security_policy` (3–10 intentos, 5–1440 min, 1–24 h, clave de 8–64). |
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
- La papelera (`deleted_record`) conserva los datos de las personas eliminadas hasta que el
  Administrador de Sistemas la vacía: defina con la empresa cada cuánto hacerlo.
- La auditoría guarda el nombre del actor y los identificadores de los registros, no sus datos;
  el texto tecleado como usuario en intentos contra cuentas inexistentes nunca se guarda.

## Pendientes de seguridad

- Retención de la auditoría y de la papelera (hoy se conservan hasta que se vacían a mano).
- Exportación de reportes de auditoría (PDF/CSV) de los mockups forenses.
- Límite de tasa (Cloudflare WAF / Rate Limiting) en la API.
- Endurecimiento del VPS (ver `docs/despliegue/vps.md`) y monitoreo de logs.
- Integración API ↔ documentos con autorización por entidad (quién puede ver qué contrato).
- Escaneo de dependencias en CI (p. ej. Dependabot) y revisión periódica de versiones.
