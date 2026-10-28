from __future__ import annotations

import httpx
import pytest
from fastapi import FastAPI

from db.connection import Database
from db.dependencies import get_database

pytestmark = pytest.mark.anyio


async def test_health_responde_ok(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "aphia-api"
    assert body["environment"] == "test"
    assert body["runtime"] == "asgi"


async def test_ready_sin_base_de_datos_configurada_responde_503(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "checks": {"database": "unavailable"}}


async def test_ready_con_base_de_datos_disponible(app: FastAPI, client: httpx.AsyncClient) -> None:
    class HealthyDatabase(Database):
        async def ping(self) -> None:
            return None

    app.dependency_overrides[get_database] = lambda: HealthyDatabase(None)

    response = await client.get("/api/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "checks": {"database": "ok"}}


async def test_ready_con_mysql_inaccesible_responde_503(
    app: FastAPI, client: httpx.AsyncClient
) -> None:
    from db.config import DatabaseConfig

    # Puerto 9 (discard): no hay MySQL escuchando, la conexión falla rápido.
    unreachable = DatabaseConfig(
        host="127.0.0.1", port=9, user="x", password="x", database="x", connect_timeout=1
    )
    app.dependency_overrides[get_database] = lambda: Database(unreachable)

    response = await client.get("/api/ready")

    assert response.status_code == 503
    assert response.json()["checks"]["database"] == "unavailable"
