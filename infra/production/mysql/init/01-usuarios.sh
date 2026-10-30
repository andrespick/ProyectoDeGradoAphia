#!/bin/bash
# Crea los usuarios de mínimo privilegio de APHIA.
# El entrypoint oficial de MySQL lo ejecuta UNA sola vez, al inicializar un volumen vacío,
# cuando la contraseña de root ya está configurada y el servidor temporal escucha solo por
# socket. Funciona tanto si el entrypoint lo carga con "source" como si lo ejecuta.
#
#   aphia_app       → usado por la API vía Hyperdrive: solo DML, exige TLS.
#   aphia_migrator  → usado por el servicio "migrator": DDL sobre la base de APHIA, exige TLS.
#
# Si este script falla, el volumen queda inicializado SIN estos usuarios y el entrypoint no
# vuelve a ejecutarlo. Corrija la causa, elimine el volumen (solo en una instalación nueva)
# y vuelva a iniciar: docker compose down && docker volume rm aphia_mysql-data

app_password="$(tr -d '\r\n' < /run/secrets/mysql_app_password)"
migrator_password="$(tr -d '\r\n' < /run/secrets/mysql_migrator_password)"

for value in "$app_password" "$migrator_password"; do
	if [[ ! "$value" =~ ^[A-Za-z0-9]{32,}$ ]]; then
		echo "01-usuarios.sh: las contraseñas deben ser alfanuméricas de 32+ caracteres (generate-secrets.sh)." >&2
		exit 1
	fi
done

if ! MYSQL_PWD="$(tr -d '\r\n' < /run/secrets/mysql_root_password)" \
	mysql --protocol=socket --user=root --database=mysql <<-EOSQL
	CREATE USER '${APHIA_APP_USER}'@'%' IDENTIFIED BY '${app_password}' REQUIRE SSL;
	GRANT SELECT, INSERT, UPDATE, DELETE ON \`${MYSQL_DATABASE}\`.* TO '${APHIA_APP_USER}'@'%';

	CREATE USER '${APHIA_MIGRATOR_USER}'@'%' IDENTIFIED BY '${migrator_password}' REQUIRE SSL;
	GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, DROP, INDEX, REFERENCES,
	      CREATE VIEW, SHOW VIEW, TRIGGER
	   ON \`${MYSQL_DATABASE}\`.* TO '${APHIA_MIGRATOR_USER}'@'%';
	EOSQL
then
	echo "01-usuarios.sh: no se pudieron crear los usuarios." >&2
	exit 1
fi

unset app_password migrator_password
echo "01-usuarios.sh: usuarios ${APHIA_APP_USER} y ${APHIA_MIGRATOR_USER} creados."
