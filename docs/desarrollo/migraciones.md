# Migraciones

Las migraciones son archivos SQL en `database/migrations/` aplicados en orden por
`database/scripts/migrate.py`. El historial queda en la tabla `schema_migrations`
(versión, nombre, checksum SHA-256, fecha).

## Agregar una migración

1. Cree `database/migrations/NNNN_descripcion.sql` con el siguiente número libre
   (la última es `0010`, así que la próxima es `0011_...`). Solo minúsculas, números y `_`.
2. Escriba una sentencia DDL por archivo cuando sea posible. Termine cada sentencia con `;`
   al final de la línea. Comentarios con `--`. No use `DELIMITER` ni procedimientos.
3. Siga las reglas físicas del [modelo de datos](../arquitectura/modelo-de-datos.md):
   tablas y columnas en inglés `snake_case`, `ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
   COLLATE=utf8mb4_0900_bin`, claves `BIGINT` con signo, FK con índice y
   `ON DELETE RESTRICT ON UPDATE RESTRICT`, importes `DECIMAL` con moneda explícita y fechas
   de operación `DATETIME(6)` en UTC.
4. Aplique y verifique:

```bash
pnpm db:status
pnpm db:migrate
pnpm test:integration
```

## Reglas

- **Nunca edite una migración aplicada.** `migrate.py` compara el checksum y se detiene si
  cambió. Corrija con una migración nueva.
- MySQL confirma implícitamente cada DDL: si una migración con dos DDL falla en la segunda,
  la primera queda aplicada. Por eso, una DDL por archivo. Excepción: las migraciones
  `0002`–`0007` crean el esquema inicial completo agrupado por dominio sobre una base vacía.
  Si una sentencia falla, `migrate.py` informa cuántas de la misma migración ya se aplicaron
  (`falló la sentencia N de M ... Las N-1 anteriores ya se aplicaron`); revise el esquema o
  restaure el respaldo antes de reintentar.
- Cambios destructivos en dos fases: (1) agregar lo nuevo y adaptar el código; (2) en una
  versión posterior, eliminar lo viejo.
- Valores de referencia que la aplicación usa por código (roles, papeles, estados, tipos de
  documento, monedas…) van en una migración con `INSERT` (como `0008`), porque producción los
  necesita. Los nombres libres (ciudades, bancos, proveedores) los crea la aplicación y solo
  se siembran en `database/seeds/` para desarrollo.
- Un candado (`GET_LOCK`) impide dos ejecuciones simultáneas.

## Producción

Las migraciones **nunca** se ejecutan al iniciar el Worker ni desde la CI. Procedimiento:

1. Ejecute y verifique un respaldo (`infra/production/backup/backup.sh`).
2. En el VPS: `docker compose --env-file .env.production --profile ops run --rm --build migrator --status`
3. Aplique: `docker compose --env-file .env.production --profile ops run --rm migrator --confirm-backup`
4. Despliegue la versión de la API compatible.

Sin `--confirm-backup`, el script se niega a migrar en `staging` y `production`. El servicio
`migrator` usa el usuario `aphia_migrator` (DDL limitado a la base de APHIA) por TLS.

## Datos ficticios

`database/seeds/*.sql` se cargan con `pnpm db:seed` (solo `APP_ENV` development o test).
Deben ser idempotentes (`INSERT ... ON DUPLICATE KEY UPDATE`) y usar dominios `.test`.
