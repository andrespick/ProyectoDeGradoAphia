"""Integridad del modelo de datos 3FN (migraciones 0002-0007) sobre MySQL real.

Reproduce los escenarios con los que se validó el DDL de referencia: casos que el modelo
debe aceptar y violaciones que MySQL debe rechazar. Cada prueba trabaja dentro de una
transacción que se revierte al final; solo se usan datos ficticios.
"""

from __future__ import annotations

from collections.abc import Iterator

import pymysql
import pytest

from dbscripts import ConnectionParams

pytestmark = pytest.mark.integration

TABLAS_DEL_MODELO = {
    # Catálogos
    "person_category", "document_type", "app_role", "city", "occupancy_state", "currency",
    "utility_type", "service_provider", "agreement_category", "party_role",
    "financial_category", "payment_state", "bank_account_category", "financial_institution",
    "file_category",
    # Entidades y relaciones
    "person", "person_document", "person_phone", "person_email", "user_account", "user_role",
    "bank_account", "property", "property_owner", "property_utility", "property_agreement",
    "agreement_party", "financial_record", "file_record", "file_person", "file_property",
    "file_agreement",
}  # fmt: skip

DATOS_BASE = [
    "INSERT INTO person (person_id, full_name) VALUES (1, 'Persona Ficticia A'), "
    "(2, 'Persona Ficticia B')",
    "INSERT INTO document_type VALUES (1, 'CO', 'CC', 'Cédula de prueba')",
    "INSERT INTO person_document VALUES (1, 1, 1, '000123')",
    "INSERT INTO currency VALUES ('COP', 'Peso de prueba')",
    "INSERT INTO property (property_id, address, rental_value, currency_code) "
    "VALUES (1, 'Dirección ficticia 1', 1000, 'COP')",
    "INSERT INTO property_owner VALUES (1, 1), (1, 2)",
    "INSERT INTO agreement_category VALUES (1, 'LEASE', 'Prueba')",
    "INSERT INTO party_role VALUES (1, 'CO_DEBTOR', 'Codeudor'), (2, 'ASSOCIATED', 'Asociado')",
    "INSERT INTO property_agreement (agreement_id, agreement_category_id, property_id, "
    "start_date) VALUES (1, 1, 1, '2026-01-01'), (2, 1, 1, '2027-01-01')",
    "INSERT INTO agreement_party VALUES (1, 1, 1), (1, 2, 1), (2, 1, 1), (1, 1, 2)",
    "INSERT INTO financial_category VALUES (1, 'REVERSAL', 'Reverso de prueba')",
    "INSERT INTO payment_state VALUES (1, 'PENDING', 'Prueba')",
    "INSERT INTO financial_record VALUES (1, 1, 1, -12.50, '2026-01-01', 1, 'COP')",
    "INSERT INTO file_category VALUES (1, 'TEST', 'Prueba')",
    "INSERT INTO file_record (file_id, file_name, file_category_id, file_path, upload_date) "
    "VALUES (1, 'soporte.pdf', 1, 'ruta/ficticia', '2026-01-01')",
    "INSERT INTO file_person VALUES (1, 1)",
    "INSERT INTO file_property VALUES (1, 1)",
    "INSERT INTO file_agreement VALUES (1, 1)",
]


@pytest.fixture
def modelo(db_params: ConnectionParams) -> Iterator[pymysql.cursors.Cursor]:
    """Cursor con los datos base cargados; todo se revierte al terminar."""
    with db_params.connect() as conn:
        try:
            with conn.cursor() as cursor:
                for statement in DATOS_BASE:
                    cursor.execute(statement)
                yield cursor
        finally:
            conn.rollback()


def _tablas(cursor: pymysql.cursors.Cursor) -> set[str]:
    cursor.execute(
        "SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE()"
    )
    return {row[0] for row in cursor.fetchall()}


def test_existen_las_32_tablas_con_colacion_binaria(db_params: ConnectionParams) -> None:
    with db_params.connect() as conn, conn.cursor() as cursor:
        assert _tablas(cursor) >= TABLAS_DEL_MODELO
        cursor.execute(
            "SELECT TABLE_NAME, TABLE_COLLATION FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA = DATABASE()"
        )
        colaciones = {name: collation for name, collation in cursor.fetchall()}
    assert {colaciones[t] for t in TABLAS_DEL_MODELO} == {"utf8mb4_0900_bin"}


def test_36_claves_foraneas_con_restrict(db_params: ConnectionParams) -> None:
    with db_params.connect() as conn, conn.cursor() as cursor:
        cursor.execute(
            "SELECT TABLE_NAME, DELETE_RULE, UPDATE_RULE "
            "FROM information_schema.REFERENTIAL_CONSTRAINTS "
            "WHERE CONSTRAINT_SCHEMA = DATABASE()"
        )
        rows = [row for row in cursor.fetchall() if row[0] in TABLAS_DEL_MODELO]
    assert len(rows) == 36
    assert {(delete, update) for _, delete, update in rows} == {("RESTRICT", "RESTRICT")}


def test_escenarios_validos(modelo: pymysql.cursors.Cursor) -> None:
    # Copropiedad: dos propietarios para el mismo inmueble.
    modelo.execute("SELECT COUNT(*) FROM property_owner WHERE property_id = 1")
    assert modelo.fetchone()[0] == 2
    # Varios codeudores en un acuerdo y una persona con varios roles y acuerdos.
    modelo.execute("SELECT COUNT(*) FROM agreement_party WHERE agreement_id = 1")
    assert modelo.fetchone()[0] == 3
    modelo.execute("SELECT COUNT(DISTINCT agreement_id) FROM agreement_party WHERE person_id = 1")
    assert modelo.fetchone()[0] == 2
    # Un archivo vinculado a persona, inmueble y acuerdo a la vez.
    modelo.execute(
        "SELECT (SELECT COUNT(*) FROM file_person WHERE file_id = 1) "
        "+ (SELECT COUNT(*) FROM file_property WHERE file_id = 1) "
        "+ (SELECT COUNT(*) FROM file_agreement WHERE file_id = 1)"
    )
    assert modelo.fetchone()[0] == 3
    # Identificador documental con ceros iniciales y movimiento negativo (reverso).
    modelo.execute("SELECT document_identifier FROM person_document WHERE person_document_id = 1")
    assert modelo.fetchone()[0] == "000123"
    modelo.execute("SELECT amount FROM financial_record WHERE record_id = 1")
    assert str(modelo.fetchone()[0]) == "-12.50"


@pytest.mark.parametrize(
    ("statement", "codigo_mysql"),
    [
        ("INSERT INTO property_owner VALUES (1, 999)", 1452),
        ("INSERT INTO agreement_party VALUES (1, 1, 1)", 1062),
        ("INSERT INTO person_document VALUES (2, 2, 1, '000123')", 1062),
        (
            "INSERT INTO property_agreement (agreement_id, agreement_category_id, property_id, "
            "start_date, end_date) VALUES (3, 1, 1, '2026-12-31', '2026-01-01')",
            3819,
        ),
        ("UPDATE property SET rental_value = -1 WHERE property_id = 1", 3819),
        ("UPDATE property SET currency_code = NULL WHERE property_id = 1", 3819),
        ("UPDATE file_record SET size_bytes = -1 WHERE file_id = 1", 3819),
        ("DELETE FROM person WHERE person_id = 1", 1451),
        (
            "INSERT INTO user_account (person_id, user_name, hashed_password) "
            "VALUES (1, 'usuario', 'x'), (2, 'usuario', 'y')",
            1062,
        ),
    ],
    ids=[
        "fk-huerfana",
        "participante-duplicado",
        "documento-duplicado-entre-personas",
        "fechas-invertidas",
        "canon-negativo",
        "canon-sin-moneda",
        "tamano-archivo-negativo",
        "borrado-con-referencias",
        "usuario-duplicado",
    ],
)
def test_violaciones_rechazadas(
    modelo: pymysql.cursors.Cursor, statement: str, codigo_mysql: int
) -> None:
    with pytest.raises(pymysql.err.MySQLError) as error:
        modelo.execute(statement)

    assert error.value.args[0] == codigo_mysql


def test_nombre_de_usuario_distingue_mayusculas(modelo: pymysql.cursors.Cursor) -> None:
    # Consecuencia de utf8mb4_0900_bin: 'Usuario' y 'usuario' son nombres distintos.
    modelo.execute(
        "INSERT INTO user_account (person_id, user_name, hashed_password) "
        "VALUES (1, 'usuario', 'x'), (2, 'Usuario', 'y')"
    )
    assert modelo.rowcount == 2
