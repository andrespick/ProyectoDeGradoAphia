"""Pruebas del lector de migraciones (sin MySQL)."""

from __future__ import annotations

from pathlib import Path

import pytest

from dbscripts import MIGRATIONS_DIR, SEEDS_DIR, ScriptError, SqlFile, discover, split_statements
from migrate import pending_migrations


def test_migraciones_del_repositorio_son_validas() -> None:
    migrations = discover(MIGRATIONS_DIR)

    assert migrations[0].version == "0001"
    for migration in migrations:
        assert migration.statements, migration.path.name


def test_seeds_del_repositorio_son_validos() -> None:
    for seed in discover(SEEDS_DIR):
        assert seed.statements


def test_split_statements_ignora_comentarios() -> None:
    sql = "-- comentario\nCREATE TABLE a (\n  id INT\n);\n\nINSERT INTO a VALUES (1);\n"

    assert split_statements(sql) == ["CREATE TABLE a (\n  id INT\n)", "INSERT INTO a VALUES (1)"]


def test_sentencia_sin_terminar_es_error() -> None:
    with pytest.raises(ScriptError):
        split_statements("CREATE TABLE a (id INT)")


def test_nombre_de_archivo_invalido(tmp_path: Path) -> None:
    (tmp_path / "crear_tabla.sql").write_text("SELECT 1;", encoding="utf-8")

    with pytest.raises(ScriptError):
        discover(tmp_path)


def test_migracion_modificada_es_rechazada(tmp_path: Path) -> None:
    migration = SqlFile("0001", "x", tmp_path / "0001_x.sql", "SELECT 1;")

    with pytest.raises(ScriptError, match="cambió"):
        pending_migrations({"0001": "otro-checksum"}, [migration])


def test_checksum_independiente_de_fin_de_linea(tmp_path: Path) -> None:
    lf = SqlFile("0001", "x", tmp_path / "a.sql", "SELECT 1;\n")
    crlf = SqlFile("0001", "x", tmp_path / "a.sql", "SELECT 1;\r\n")

    assert lf.checksum == crlf.checksum
