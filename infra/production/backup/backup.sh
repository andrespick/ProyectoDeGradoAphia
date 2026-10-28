#!/usr/bin/env bash
# Respaldo cifrado de APHIA: base de datos MySQL + volumen de documentos.
#
# Requisitos en el VPS: docker, age (cifrado); rclone solo si se configura un destino externo.
# Configuración: infra/production/backup/backup.env (ver backup.env.example).
# Programación sugerida (cron, diario 03:15 UTC):
#   15 3 * * * /opt/aphia/infra/production/backup/backup.sh >> /var/log/aphia-backup.log 2>&1
set -euo pipefail

BACKUP_DIR="$(cd "$(dirname "$0")" && pwd)"
PRODUCTION_DIR="$(dirname "$BACKUP_DIR")"
# shellcheck source=/dev/null
source "${BACKUP_DIR}/backup.env"

: "${BACKUP_AGE_RECIPIENT:?Defina BACKUP_AGE_RECIPIENT (clave pública age)}"
LOCAL_DIR="${BACKUP_LOCAL_DIR:-/var/backups/aphia}"
LOCAL_RETENTION_DAYS="${BACKUP_LOCAL_RETENTION_DAYS:-14}"
REMOTE="${BACKUP_RCLONE_REMOTE:-}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"

compose() {
	docker compose --project-directory "$PRODUCTION_DIR" --env-file "$PRODUCTION_DIR/.env.production" "$@"
}

stamp="$(date -u +%Y%m%dT%H%M%SZ)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
umask 077

echo "[$(date -u +%FT%TZ)] Iniciando respaldo ${stamp}"

# 1. MySQL: volcado consistente sin bloquear tablas InnoDB.
compose exec -T mysql sh -c '
	MYSQL_PWD="$(cat /run/secrets/mysql_root_password)" exec mysqldump \
		--user=root --single-transaction --routines --triggers --events \
		--set-gtid-purged=OFF --databases "$MYSQL_DATABASE"' \
	| gzip -9 > "${work}/mysql.sql.gz"

# 2. Documentos: archivo tar del volumen (contenido + metadatos).
compose exec -T files tar -C /data -cf - . | gzip -6 > "${work}/documentos.tar.gz"

# 3. Manifiesto con sumas de verificación.
(cd "$work" && sha256sum mysql.sql.gz documentos.tar.gz > SHA256SUMS)

# 4. Empaquetar y cifrar. Solo quien tenga la clave privada age podrá restaurarlo.
archive="${work}/aphia-${stamp}.tar.age"
tar -C "$work" -cf - mysql.sql.gz documentos.tar.gz SHA256SUMS | age -r "$BACKUP_AGE_RECIPIENT" -o "$archive"

# 5. Copia local diaria en un directorio restringido (solo root) con retención propia.
install -d -m 700 "$LOCAL_DIR"
install -m 600 "$archive" "$LOCAL_DIR/"
find "$LOCAL_DIR" -maxdepth 1 -name 'aphia-*.tar.age' -mtime +"$LOCAL_RETENTION_DAYS" -delete
echo "[$(date -u +%FT%TZ)] Copia local: ${LOCAL_DIR}/aphia-${stamp}.tar.age (retención ${LOCAL_RETENTION_DAYS} días)"

# 6. Copia fuera del VPS (opcional) y su retención. La copia local no sobrevive a la pérdida del VPS.
if [ -n "$REMOTE" ]; then
	rclone copy "$archive" "$REMOTE/"
	rclone delete --min-age "${RETENTION_DAYS}d" "$REMOTE/"
	echo "[$(date -u +%FT%TZ)] Copia externa: ${REMOTE}/ (retención ${RETENTION_DAYS} días)"
else
	echo "[$(date -u +%FT%TZ)] AVISO: sin BACKUP_RCLONE_REMOTE; solo existe la copia local"
fi

echo "[$(date -u +%FT%TZ)] Respaldo completado: aphia-${stamp}.tar.age ($(du -h "$archive" | cut -f1))"
