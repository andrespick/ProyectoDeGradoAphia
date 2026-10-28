"""Carga los datos ficticios de database/seeds (solo development y test).

Uso: pnpm db:seed
"""

from __future__ import annotations

import os
import sys

import pymysql

from dbscripts import SEEDS_DIR, ConnectionParams, ScriptError, discover

ALLOWED_ENVIRONMENTS = {"development", "test"}


def apply_seeds(conn: pymysql.connections.Connection) -> int:
    seeds = discover(SEEDS_DIR)
    try:
        with conn.cursor() as cursor:
            for seed in seeds:
                for statement in seed.statements:
                    cursor.execute(statement)
                print(f"  cargado {seed.path.name}")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return len(seeds)


def main() -> int:
    app_env = os.environ.get("APP_ENV", "development")
    if app_env not in ALLOWED_ENVIRONMENTS:
        print(f"ERROR: los datos ficticios no se cargan en APP_ENV={app_env}.", file=sys.stderr)
        return 2
    try:
        params = ConnectionParams.from_env()
        with params.connect() as conn:
            count = apply_seeds(conn)
        print(f"{count} archivo(s) de datos ficticios cargados en {params.database}.")
        return 0
    except (ScriptError, pymysql.err.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
