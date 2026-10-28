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
| Roles en endpoints (`require_roles`) y respuesta 401 cuando no hay autenticación real | `modules/auth` | ✅ |
| Servicio de documentos: token de servicio (comparación en tiempo constante), tipo por firma, tamaño máximo, ids UUID, sin *path traversal*, sin sobrescritura, contenedor sin privilegios y de solo lectura | `apps/files` | ✅ |
| MySQL y documentos sin puertos públicos; red interna sin salida a Internet; TLS obligatorio a MySQL | `infra/production/compose.yaml`, `aphia.cnf` | ✅ (en réplica local) |
| Bases separadas por entorno (desarrollo, pruebas, staging, producción) | Compose, Hyperdrive por entorno | Parcial (staging/prod por crear) |
| Despliegue a producción solo con aprobación y desde `main` | `.github/workflows/deploy.yml` | Configurado, no ejecutado |
| Respaldos cifrados con `age` fuera del VPS | `infra/production/backup` | Comandos de volcado verificados; ciclo completo no ejecutado |

## Autenticación: estado y límites

**No existe autenticación de producción.** `AUTH_MODE=development` entrega un usuario
ficticio con rol `admin` únicamente si `APP_ENV` es `development` o `test`; la configuración
falla si se intenta activar en staging o producción, y la dependencia vuelve a comprobarlo.
En staging/producción todos los endpoints de negocio responden **401** hasta implementar:

1. Proveedor de identidad (opciones a evaluar: Cloudflare Access para personal interno,
   o un IdP OIDC). Para una empresa pequeña con usuarios internos, **Cloudflare Access**
   delante de Pages y la API es la opción de menor costo y mantenimiento: la API validaría
   el JWT `Cf-Access-Jwt-Assertion` y mapearía el correo a roles en MySQL.
2. Tabla de usuarios/roles y auditoría (trazabilidad) en MySQL.
3. Reemplazar `get_current_principal` sin cambiar los routers (ya dependen de `require_roles`).

## Manejo de secretos

| Secreto | Desarrollo | Producción |
| --- | --- | --- |
| Contraseñas MySQL | `.env` (generado) | `infra/production/secrets/` en el VPS (generate-secrets.sh) |
| Contraseña `aphia_app` para Hyperdrive | — | Configuración de Hyperdrive (Cloudflare) |
| Token del servicio de documentos | `.env` | `secrets/files_service_token` + `wrangler secret put FILES_SERVICE_TOKEN` |
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

- Autenticación real y autorización por rol con usuarios en MySQL; auditoría de acciones.
- Límite de tasa (Cloudflare WAF / Rate Limiting) en la API.
- Endurecimiento del VPS (ver `docs/despliegue/vps.md`) y monitoreo de logs.
- Integración API ↔ documentos con autorización por entidad (quién puede ver qué contrato).
- Escaneo de dependencias en CI (p. ej. Dependabot) y revisión periódica de versiones.
