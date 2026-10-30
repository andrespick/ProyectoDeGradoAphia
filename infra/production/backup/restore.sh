#!/usr/bin/env bash
# Restaura un respaldo cifrado de APHIA (MySQL + documentos).
#
# Uso:
#   restore.sh <archivo.tar.age | nombre en el remoto> <identidad-age.txt> --confirm
#
# ADVERTENCIA: reemplaza la base de datos y los documentos actuales. Antes de restaurar en
# producción, haga un respaldo del estado actual (backup.sh) y detenga el tráfico de la API.
# Procedimiento completo: docs/despliegue/restauracion.md
set -euo pipefail

if [[ $# -lt 3 || "$3" != "--confirm" ]]; then
	echo "Uso: $0 <archivo.tar.age> <identidad-age.txt> --confirm" >&2
	exit 2
fi

BACKUP_DIR="$(cd "$(dirname "$0")" && pwd)"
PRODUCTION_DIR="$(dirname "$BACKUP_DIR")"
source_archive="$1"
identity="$2"

compose() {
	docker compose --project-directory "$PRODUCTION_DIR" --env-file "$PRODUCTION_DIR/.env.production" "$@"
}

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
umask 077

if [[ ! -f "$source_archive" ]]; then
	# shellcheck source=/dev/null
	source "${BACKUP_DIR}/backup.env"
	echo "Descargando ${source_archive} desde ${BACKUP_RCLONE_REMOTE}"
	rclone copy "${BACKUP_RCLONE_REMOTE}/${source_archive}" "$work/"
	source_archive="${work}/$(basename "$source_archive")"
fi

echo "Descifrando y verificando integridad"
age -d -i "$identity" "$source_archive" | tar -C "$work" -xf -
(cd "$work" && sha256sum -c SHA256SUMS)

echo "Restaurando MySQL"
gunzip -c "${work}/mysql.sql.gz" | compose exec -T mysql sh -c '
	MYSQL_PWD="$(cat /run/secrets/mysql_root_password)" exec mysql --user=root'

echo "Restaurando documentos"
compose stop files
compose run --rm --no-deps --user 10001 -v "${work}:/restore:ro" --entrypoint sh files -c '
	find /data -mindepth 1 -delete && tar -C /data -xzf /restore/documentos.tar.gz'
compose start files

echo "Restauración completada. Verifique /api/ready y una descarga de documento."
