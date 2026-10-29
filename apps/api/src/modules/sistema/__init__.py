"""Estado del sistema y respaldos para el Administrador de Sistemas.

El panel reúne la API (versión, entorno, runtime), MySQL (latencia, versión, tamaño), las
migraciones aplicadas (``schema_migrations``), conteos de registros y el último respaldo.
Los respaldos los ejecuta ``infra/production/backup/backup.sh`` en el VPS y los registra en
``backup_run`` (0017); la API solo lee ese historial y anota solicitudes manuales que el script
atiende en su siguiente ejecución programada. La API nunca ejecuta comandos en el servidor.
"""
