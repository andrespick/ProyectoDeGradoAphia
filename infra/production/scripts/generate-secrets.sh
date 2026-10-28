#!/usr/bin/env bash
# Genera los secretos de producción en infra/production/secrets/ (solo si no existen).
# Ejecutar EN EL VPS. Guarde una copia cifrada fuera del servidor (gestor de contraseñas).
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p secrets
chmod 700 secrets

for name in mysql_root_password mysql_app_password mysql_migrator_password files_service_token; do
	target="secrets/${name}"
	if [[ -s "$target" ]]; then
		echo "existe: ${target} (no se modifica)"
		continue
	fi
	# Sin salto de línea final (y sin \r en Git Bash para Windows).
	openssl rand -hex 32 | tr -d '\r\n' > "$target"
	echo "creado: ${target}"
done

# Los contenedores leen los archivos con usuarios no root (mysql, aphia). El directorio
# padre (700) impide que otros usuarios del host los lean.
chmod 644 secrets/*
