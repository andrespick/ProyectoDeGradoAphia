#!/usr/bin/env bash
# Respaldo cifrado de APHIA: base de datos MySQL + volumen de documentos.
#
# Requisitos en el VPS: docker, age (cifrado), flock; rclone solo si se configura un destino externo.
# Configuración: infra/production/backup/backup.env (ver backup.env.example).
# Cada ejecución queda en la tabla backup_run, que el Administrador de Sistemas ve en la web.
#
# Programación sugerida (cron):
#   15 3 * * *   /opt/aphia/infra/production/backup/backup.sh               >> /var/log/aphia-backup.log 2>&1
#   */5 * * * *  /opt/aphia/infra/production/backup/backup.sh --solicitudes >> /var/log/aphia-backup.log 2>&1
# La segunda línea atiende los respaldos solicitados desde la web («Solicitar respaldo»); si no hay
# ninguno pendiente termina sin hacer nada.
set -Eeuo pipefail

BACKUP_DIR="$(cd "$(dirname "$0")" && pwd)"
PRODUCTION_DIR="$(dirname "$BACKUP_DIR")"
# shellcheck source=/dev/null
source "${BACKUP_DIR}/backup.env"

: "${BACKUP_AGE_RECIPIENT:?Defina BACKUP_AGE_RECIPIENT (clave pública age)}"
LOCAL_DIR="${BACKUP_LOCAL_DIR:-/var/backups/aphia}"
LOCAL_RETENTION_DAYS="${BACKUP_LOCAL_RETENTION_DAYS:-14}"
REMOTE="${BACKUP_RCLONE_REMOTE:-}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
LOCK_FILE="${BACKUP_LOCK_FILE:-/var/lock/aphia-backup.lock}"

compose() {
	docker compose --project-directory "$PRODUCTION_DIR" --env-file "$PRODUCTION_DIR/.env.production" "$@"
}

# Ejecuta SQL en la base de APHIA. Solo recibe texto fijo de este script y números leídos de la
# propia base (nunca datos de usuarios).
sql() {
	printf '%s\n' "$1" | compose exec -T mysql sh -c '
		MYSQL_PWD="$(cat /run/secrets/mysql_root_password)" exec mysql \
			--user=root --default-character-set=utf8mb4 --batch --skip-column-names "$MYSQL_DATABASE"'
}

# Un solo respaldo a la vez (el programado y el solicitado pueden coincidir).
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
	echo "[$(date -u +%FT%TZ)] Otro respaldo está en curso; se omite esta ejecución"
	exit 0
fi

# Con el candado tomado, un registro EN_CURSO es de una ejecución que se interrumpió.
sql "UPDATE backup_run SET status = 'FALLIDO', finished_at = UTC_TIMESTAMP(6), error_message = 'Interrumpido antes de terminar' WHERE status = 'EN_CURSO';"

if [ "${1:-}" = "--solicitudes" ]; then
	run_id="$(sql "SELECT backup_run_id FROM backup_run WHERE status = 'SOLICITADO' ORDER BY backup_run_id LIMIT 1;")"
	[ -n "$run_id" ] || exit 0
	sql "UPDATE backup_run SET status = 'EN_CURSO', started_at = UTC_TIMESTAMP(6) WHERE backup_run_id = ${run_id};"
else
	run_id="$(sql "INSERT INTO backup_run (trigger_type, status, started_at) VALUES ('PROGRAMADO', 'EN_CURSO', UTC_TIMESTAMP(6)); SELECT LAST_INSERT_ID();")"
fi

paso="preparación"
registrar_fallo() {
	sql "UPDATE backup_run SET status = 'FALLIDO', finished_at = UTC_TIMESTAMP(6), error_message = 'Falló: ${paso}' WHERE backup_run_id = ${run_id};" || true
	echo "[$(date -u +%FT%TZ)] ERROR en el respaldo #${run_id} (${paso})"
}
trap registrar_fallo ERR

stamp="$(date -u +%Y%m%dT%H%M%SZ)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
umask 077

echo "[$(date -u +%FT%TZ)] Iniciando respaldo #${run_id} (${stamp})"

# 1. MySQL: volcado consistente sin bloquear tablas InnoDB.
paso="volcado de MySQL"
compose exec -T mysql sh -c '
	MYSQL_PWD="$(cat /run/secrets/mysql_root_password)" exec mysqldump \
		--user=root --single-transaction --routines --triggers --events \
		--set-gtid-purged=OFF --databases "$MYSQL_DATABASE"' \
	| gzip -9 > "${work}/mysql.sql.gz"

# 2. Documentos: archivo tar del volumen (contenido + metadatos).
paso="copia de documentos"
compose exec -T files tar -C /data -cf - . | gzip -6 > "${work}/documentos.tar.gz"

# 3. Manifiesto con sumas de verificación.
(cd "$work" && sha256sum mysql.sql.gz documentos.tar.gz > SHA256SUMS)

# 4. Empaquetar y cifrar. Solo quien tenga la clave privada age podrá restaurarlo.
paso="cifrado"
archive="${work}/aphia-${stamp}.tar.age"
tar -C "$work" -cf - mysql.sql.gz documentos.tar.gz SHA256SUMS | age -r "$BACKUP_AGE_RECIPIENT" -o "$archive"

# 5. Copia local diaria en un directorio restringido (solo root) con retención propia.
paso="copia local"
install -d -m 700 "$LOCAL_DIR"
install -m 600 "$archive" "$LOCAL_DIR/"
find "$LOCAL_DIR" -maxdepth 1 -name 'aphia-*.tar.age' -mtime +"$LOCAL_RETENTION_DAYS" -delete
echo "[$(date -u +%FT%TZ)] Copia local: ${LOCAL_DIR}/aphia-${stamp}.tar.age (retención ${LOCAL_RETENTION_DAYS} días)"

# 6. Copia fuera del VPS (opcional) y su retención. La copia local no sobrevive a la pérdida del VPS.
remote_copy=0
if [ -n "$REMOTE" ]; then
	paso="copia externa"
	rclone copy "$archive" "$REMOTE/"
	rclone delete --min-age "${RETENTION_DAYS}d" "$REMOTE/"
	remote_copy=1
	echo "[$(date -u +%FT%TZ)] Copia externa: ${REMOTE}/ (retención ${RETENTION_DAYS} días)"
else
	echo "[$(date -u +%FT%TZ)] AVISO: sin BACKUP_RCLONE_REMOTE; solo existe la copia local"
fi

paso="registro del resultado"
size="$(stat -c %s "$archive")"
sql "UPDATE backup_run SET status = 'OK', finished_at = UTC_TIMESTAMP(6), file_name = 'aphia-${stamp}.tar.age', size_bytes = ${size}, remote_copy = ${remote_copy} WHERE backup_run_id = ${run_id};"
echo "[$(date -u +%FT%TZ)] Respaldo #${run_id} completado: aphia-${stamp}.tar.age ($(du -h "$archive" | cut -f1))"
