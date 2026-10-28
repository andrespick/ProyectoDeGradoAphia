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
            cursor.execute("DELETE FROM clientes")
        conn.commit()
        yield conn


def settings_for(params: ConnectionParams) -> Settings:
    return Settings(
        app_env="test",
        cors_origins=("http://localhost:5173",),
        auth_mode="development",
        db_host=params.host,
        db_port=params.port,
        db_name=params.database,
        db_user=params.user,
        db_password=params.password,
    )


@pytest.fixture
def app(db_params: ConnectionParams, db_conn: pymysql.connections.Connection) -> FastAPI:
    return create_app(settings_for(db_params))


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as http:
        yield http
