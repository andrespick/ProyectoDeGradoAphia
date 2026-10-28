"""Aplica las migraciones SQL versionadas de database/migrations.

Uso (desde la raíz del repositorio):
    pnpm db:migrate             # aplica las pendientes
    pnpm db:status              # muestra el estado sin aplicar nada

Reglas:
- Una migración aplicada nunca se modifica: se valida su checksum SHA-256.
- Un candado de MySQL (GET_LOCK) evita ejecuciones simultáneas.
- MySQL confirma implícitamente cada sentencia DDL: una migración con varias sentencias
  DDL no es atómica. Preferir una sola sentencia DDL por migración. Si una sentencia
  falla, el error indica cuáles de la misma migración ya quedaron aplicadas.
- En APP_ENV=production o staging se exige --confirm-backup (respaldo previo verificado).
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence

import pymysql

from dbscripts import MIGRATIONS_DIR, ConnectionParams, ScriptError, SqlFile, discover

LOCK_NAME = "aphia_migrations"
PROTECTED_ENVIRONMENTS = {"staging", "production"}

_CREATE_HISTORY = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version     CHAR(4)      NOT NULL,
    nombre      VARCHAR(200) NOT NULL,
    checksum    CHAR(64)     NOT NULL,
    aplicada_en DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (version)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4
"""


def applied_migrations(conn: pymysql.connections.Connection) -> dict[str, str]:
    with conn.cursor() as cursor:
        cursor.execute(_CREATE_HISTORY)
        cursor.execute("SELECT version, checksum FROM schema_migrations")
        return {version: checksum for version, checksum in cursor.fetchall()}


def pending_migrations(applied: dict[str, str], migrations: Sequence[SqlFile]) -> list[SqlFile]:
    pending: list[SqlFile] = []
    for migration in migrations:
        checksum = applied.get(migration.version)
        if checksum is None:
            pending.append(migration)
        elif checksum != migration.checksum:
            raise ScriptError(
                f"La migración {migration.path.name} cambió después de aplicarse. "
                "Cree una migración nueva en lugar de editar una existente."
            )
    return pending


def apply_migrations(
    conn: pymysql.connections.Connection, migrations: Sequence[SqlFile] | None = None
) -> list[SqlFile]:
    migrations = discover(MIGRATIONS_DIR) if migrations is None else migrations
    with conn.cursor() as cursor:
        cursor.execute("SELECT GET_LOCK(%s, 30)", (LOCK_NAME,))
        if cursor.fetchone()[0] != 1:
            raise ScriptError("Otra ejecución de migraciones está en curso.")
    try:
        pending = pending_migrations(applied_migrations(conn), migrations)
        for migration in pending:
            with conn.cursor() as cursor:
                statements = migration.statements
                for number, statement in enumerate(statements, start=1):
                    try:
                        cursor.execute(statement)
                    except pymysql.err.MySQLError as exc:
                        raise ScriptError(
                            f"{migration.path.name}: falló la sentencia {number} de "
                            f"{len(statements)} ({_summary(statement)}): {exc}. "
                            f"Las {number - 1} anteriores ya se aplicaron (DDL no transaccional); "
                            "revise el esquema antes de reintentar o restaure el respaldo."
                        ) from exc
                cursor.execute(
                    "INSERT INTO schema_migrations (version, nombre, checksum) VALUES (%s, %s, %s)",
                    (migration.version, migration.name, migration.checksum),
                )
            conn.commit()
            print(f"  aplicada {migration.path.name}")
        return pending
    except Exception:
        conn.rollback()
        raise
    finally:
        with conn.cursor() as cursor:
            cursor.execute("SELECT RELEASE_LOCK(%s)", (LOCK_NAME,))


def _summary(statement: str) -> str:
    first_line = statement.strip().split("\n", 1)[0]
    return first_line[:80]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--status", action="store_true", help="solo mostrar el estado")
    parser.add_argument(
        "--confirm-backup",
        action="store_true",
        help="obligatorio en staging/production: confirma que existe un respaldo verificado",
    )
    args = parser.parse_args(argv)

    app_env = os.environ.get("APP_ENV", "development")
    try:
        params = ConnectionParams.from_env()
        migrations = discover(MIGRATIONS_DIR)
        with params.connect() as conn:
            pending = pending_migrations(applied_migrations(conn), migrations)
            print(f"Base de datos {params.database} en {params.host}:{params.port} ({app_env})")
            print(f"  {len(migrations) - len(pending)} aplicadas, {len(pending)} pendientes")
            for migration in pending:
                print(f"  pendiente {migration.path.name}")
            if args.status or not pending:
                return 0
            if app_env in PROTECTED_ENVIRONMENTS and not args.confirm_backup:
                print(
                    "ERROR: en staging/production ejecute primero un respaldo "
                    "y use --confirm-backup."
                )
                return 2
            apply_migrations(conn, migrations)
            print("Migraciones aplicadas correctamente.")
            return 0
    except (ScriptError, pymysql.err.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
