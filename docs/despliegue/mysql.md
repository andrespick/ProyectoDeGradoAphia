# MySQL en producción

Servicio `mysql` de `infra/production/compose.yaml`, imagen `mysql:8.4`, configuración en
`infra/production/mysql/conf.d/aphia.cnf`.

## Usuarios (creados por `mysql/init/01-usuarios.sh` al inicializar el volumen)

| Usuario | Permisos | Uso |
| --- | --- | --- |
| `root` | Todos | Administración y respaldos, solo desde el contenedor |
| `aphia_app` | `SELECT, INSERT, UPDATE, DELETE` sobre `aphia.*`, `REQUIRE SSL` | API vía Hyperdrive |
| `aphia_migrator` | DDL + DML sobre `aphia.*`, `REQUIRE SSL` | Servicio `migrator` |

Verificado en una réplica local: sin TLS se rechaza la conexión; con TLS se negocia TLSv1.3;
`aphia_app` no puede ejecutar `DROP`.

Si el script de inicialización falla, el volumen queda creado **sin** estos usuarios y no se
reintenta. En una instalación nueva: `docker compose down`, `docker volume rm aphia_mysql-data`,
corregir la causa y volver a iniciar.

## Configuración relevante

- `require_secure_transport = ON`, `local_infile = OFF`, TLS 1.2/1.3.
- `innodb_buffer_pool_size = 512M`, `max_connections = 60`, `performance_schema = OFF`
  (VPS de 2 GB). Con 4 GB: buffer pool 1G y `MYSQL_MEMORY_LIMIT=2000m`.
- Zona horaria UTC; `utf8mb4_0900_ai_ci`.
- `slow_query_log` con umbral de 2 s.

## Migraciones (siempre manuales y con respaldo previo)

```bash
cd /opt/aphia/infra/production
../production/backup/backup.sh                       # 1. respaldo verificado
docker compose --env-file .env.production --profile ops run --rm --build migrator --status
docker compose --env-file .env.production --profile ops run --rm migrator --confirm-backup
```

Detalle de reglas: [docs/desarrollo/migraciones.md](../desarrollo/migraciones.md).

## Bases por entorno

Use instancias o bases distintas para staging y producción (por ejemplo `aphia_staging` en el
mismo VPS con su propio usuario y configuración de Hyperdrive, o un segundo VPS). Nunca
apunte staging a la base de producción.

## Consola de administración

```bash
docker compose --env-file .env.production exec mysql \
  sh -c 'MYSQL_PWD="$(cat /run/secrets/mysql_root_password)" mysql -uroot aphia'
```
