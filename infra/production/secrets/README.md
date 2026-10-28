# Secretos de producción

Este directorio contiene, **solo en el VPS**, los archivos que `compose.yaml` monta como
Docker secrets. Ninguno se versiona (ver `.gitignore`).

| Archivo                   | Uso                                                      |
| ------------------------- | -------------------------------------------------------- |
| `mysql_root_password`     | Usuario `root` de MySQL (solo administración y respaldos) |
| `mysql_app_password`      | Usuario `aphia_app` (API vía Hyperdrive)                  |
| `mysql_migrator_password` | Usuario `aphia_migrator` (migraciones)                    |
| `files_service_token`     | Token entre la API y el servicio de documentos            |

Generarlos con `infra/production/scripts/generate-secrets.sh`. La contraseña de
`aphia_app` también se registra en la configuración de Hyperdrive, y el token de documentos
como secreto del Worker (`wrangler secret put FILES_SERVICE_TOKEN`).
