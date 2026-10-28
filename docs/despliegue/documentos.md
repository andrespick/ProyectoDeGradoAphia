# Servicio de documentos en producción

Servicio `files` de `infra/production/compose.yaml`, construido desde `apps/files`.

## Configuración

| Variable | Valor en producción |
| --- | --- |
| `FILES_SERVICE_TOKEN_FILE` | `/run/secrets/files_service_token` (Docker secret) |
| `FILES_STORAGE_DIR` | `/data` (volumen `aphia_files-data`) |
| `FILES_MAX_BYTES` | `10485760` (10 MiB) por defecto |
| `FILES_ALLOWED_TYPES` | `application/pdf,image/png,image/jpeg` |

El servicio se niega a iniciar si el token tiene menos de 32 caracteres.

## Aislamiento

- Sin puertos publicados; red `backend` interna (sin salida a Internet). Verificado en réplica local.
- Usuario sin privilegios (uid 10001), sistema de archivos de solo lectura salvo `/data` y
  `/tmp`, `cap_drop: ALL`, `no-new-privileges`.
- Solo `cloudflared` lo alcanza; Cloudflare lo expone al Worker como servicio HTTP de
  Workers VPC (ver [túnel](tunnel-y-acceso-privado.md)). El usuario final nunca lo llama.

## API del servicio

| Método y ruta | Descripción |
| --- | --- |
| `GET /health` | Estado (sin token) |
| `POST /v1/files` | Cuerpo binario; `Content-Type` y `X-Filename` (URL-encoded) opcionales → 201 con metadatos |
| `GET /v1/files/{id}` | Descarga (`Content-Disposition: attachment`) |
| `GET /v1/files/{id}/metadata` | Metadatos |
| `DELETE /v1/files/{id}` | Eliminación → 204 |

Todas salvo `/health` requieren `Authorization: Bearer <token>`.

## Persistencia y respaldo

Los archivos sobreviven a `docker compose up --force-recreate` y a actualizaciones de imagen
(verificado en desarrollo). El respaldo diario incluye el volumen completo
([restauración](restauracion.md)).

## Rotación del token

1. Genere un valor nuevo en `secrets/files_service_token`.
2. `docker compose --env-file .env.production up -d files`
3. `uv run pywrangler secret put FILES_SERVICE_TOKEN --env production` (en `apps/api`).
