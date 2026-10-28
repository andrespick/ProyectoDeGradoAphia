"""Fixtures de integración: MySQL de pruebas (contenedor mysql-test, base *_test).

Variables: TEST_DB_HOST, TEST_DB_PORT, TEST_DB_NAME, TEST_DB_USER, TEST_DB_PASSWORD.
``pnpm test:integration`` levanta el contenedor y define estas variables.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Iterator

import httpx
import pymysql
import pytest
from fastapi import FastAPI

from core.config import Settings
from dbscripts import ConnectionParams
from main import create_app
from migrate import apply_migrations

SECRET = "secreto-de-integracion-de-al-menos-32-caracteres"

# Orden de borrado compatible con las FK RESTRICT (hijas antes que padres).
TABLAS_A_LIMPIAR = [
    "file_agreement",
    "file_person",
    "file_property",
    "file_record",
    "financial_record",
    "agreement_party",
    "property_agreement",
    "property_utility",
    "property_owner",
    "property",
    "bank_account",
    "person_party_role",
    "user_role",
    "user_account",
    "person_email",
    "person_phone",
    "person_document",
    "person",
    "city",
    "service_provider",
    "financial_institution",
]


def _params() -> ConnectionParams:
    required = ["TEST_DB_NAME", "TEST_DB_USER", "TEST_DB_PASSWORD"]
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        pytest.fail(
            f"Faltan {', '.join(missing)}. Ejecute las pruebas con: pnpm test:integration",
            pytrace=False,
        )
    database = os.environ["TEST_DB_NAME"]
    if not database.endswith("_test"):
        pytest.fail("TEST_DB_NAME debe terminar en _test (las pruebas borran datos).")
    return ConnectionParams(
        host=os.environ.get("TEST_DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("TEST_DB_PORT", "3308")),
        database=database,
        user=os.environ["TEST_DB_USER"],
        password=os.environ["TEST_DB_PASSWORD"],
    )


@pytest.fixture(scope="session")
def db_params() -> Iterator[ConnectionParams]:
    params = _params()
    with params.connect() as conn:
        apply_migrations(conn)
    yield params


@pytest.fixture
def db_conn(db_params: ConnectionParams) -> Iterator[pymysql.connections.Connection]:
    with db_params.connect() as conn:
        with conn.cursor() as cursor:
            for tabla in TABLAS_A_LIMPIAR:
                cursor.execute(f"DELETE FROM {tabla}")  # noqa: S608 - lista fija
        conn.commit()
        yield conn


def settings_for(params: ConnectionParams, **overrides: object) -> Settings:
    values: dict[str, object] = {
        "app_env": "test",
        "cors_origins": ("http://localhost:5173",),
        "auth_mode": "development",
        "db_host": params.host,
        "db_port": params.port,
        "db_name": params.database,
        "db_user": params.user,
        "db_password": params.password,
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


@pytest.fixture
def app(db_params: ConnectionParams, db_conn: pymysql.connections.Connection) -> FastAPI:
    return create_app(settings_for(db_params))


@pytest.fixture
def db_app(db_params: ConnectionParams, db_conn: pymysql.connections.Connection) -> FastAPI:
    """Modo database: inicio de sesión real contra MySQL."""
    return create_app(settings_for(db_params, auth_mode="database", auth_secret=SECRET))


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as http:
        yield http


@pytest.fixture
async def db_client(db_app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=db_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as http:
        yield http


def crear_cuenta(
    conn: pymysql.connections.Connection,
    user_name: str,
    hashed_password: str,
    rol: str = "ADMIN_SISTEMAS",
    identificacion: str | None = None,
) -> int:
    """Inserta persona + documento + cuenta + rol por SQL y devuelve el account_id."""
    with conn.cursor() as cursor:
        cursor.execute("INSERT INTO person (full_name) VALUES (%s)", (f"Persona {user_name}",))
        person_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO person_document (person_id, document_type_id, document_identifier) "
            "SELECT %s, document_type_id, %s FROM document_type "
            "WHERE issuer_scope = 'CO' AND code = 'CC'",
            (person_id, identificacion or f"9{person_id:08d}"),
        )
        cursor.execute(
            "INSERT INTO user_account (person_id, user_name, login_email, hashed_password) "
            "VALUES (%s, %s, %s, %s)",
            (person_id, user_name, f"{user_name}@example.test", hashed_password),
        )
        account_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO user_role (account_id, role_id) "
            "SELECT %s, role_id FROM app_role WHERE code = %s",
            (account_id, rol),
        )
    conn.commit()
    return int(account_id)
