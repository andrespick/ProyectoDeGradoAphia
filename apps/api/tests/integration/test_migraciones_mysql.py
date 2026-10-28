from __future__ import annotations

from pathlib import Path

import pytest

from dbscripts import ConnectionParams, ScriptError, SqlFile
from migrate import apply_migrations

pytestmark = pytest.mark.integration


def test_fallo_parcial_informa_las_sentencias_ya_aplicadas(
    db_params: ConnectionParams, tmp_path: Path
) -> None:
    sql = (
        "CREATE TABLE prueba_fallo_parcial (id INT PRIMARY KEY);\n"
        "CREATE TABLE prueba_fallo_parcial (id INT);\n"
    )
    migration = SqlFile("9999", "prueba_fallo", tmp_path / "9999_prueba_fallo.sql", sql)

    with db_params.connect() as conn:
        try:
            with pytest.raises(ScriptError, match=r"sentencia 2 de 2.*Las 1 anteriores ya se"):
                apply_migrations(conn, [migration])

            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM schema_migrations WHERE version = '9999'")
                assert cursor.fetchone()[0] == 0  # no se registra como aplicada
                cursor.execute("SHOW TABLES LIKE 'prueba_fallo_parcial'")
                assert cursor.fetchone() is not None  # la primera DDL sí quedó aplicada
        finally:
            with conn.cursor() as cursor:
                cursor.execute("DROP TABLE IF EXISTS prueba_fallo_parcial")
