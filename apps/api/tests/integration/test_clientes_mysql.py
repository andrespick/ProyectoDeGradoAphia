from __future__ import annotations

import httpx
import pymysql
import pytest

from dbscripts import ConnectionParams
from main import create_app
from migrate import apply_migrations
from tests.integration.conftest import settings_for

pytestmark = [pytest.mark.integration, pytest.mark.anyio]


async def test_ready_con_mysql_real(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/ready")

    assert response.status_code == 200
    assert response.json()["checks"]["database"] == "ok"


async def test_crear_cliente_persiste_en_mysql(
    client: httpx.AsyncClient, db_conn: pymysql.connections.Connection
) -> None:
    response = await client.post(
        "/api/v1/clientes", json={"nombre": "Cliente Integración", "correo": "INT@example.test"}
    )

    assert response.status_code == 201
    created = response.json()

    with db_conn.cursor() as cursor:
        cursor.execute(
            "SELECT nombre, correo, creado_en, actualizado_en FROM clientes WHERE id = %s",
            (created["id"],),
        )
        row = cursor.fetchone()
    assert row is not None
    assert row[0] == "Cliente Integración"
    assert row[1] == "int@example.test"
    assert row[2] is not None and row[3] is not None


async def test_listar_clientes_desde_mysql(client: httpx.AsyncClient) -> None:
    for i in range(3):
        await client.post(
            "/api/v1/clientes", json={"nombre": f"Cliente {i}", "correo": f"lista{i}@example.test"}
        )

    response = await client.get("/api/v1/clientes?limit=2")

    page = response.json()
    assert page["total"] == 3
    assert [c["correo"] for c in page["items"]] == ["lista2@example.test", "lista1@example.test"]


async def test_datos_persisten_entre_instancias_de_la_api(
    db_params: ConnectionParams, db_conn: pymysql.connections.Connection
) -> None:
    transport = httpx.ASGITransport(app=create_app(settings_for(db_params)))
    async with httpx.AsyncClient(transport=transport, base_url="http://a") as first:
        await first.post(
            "/api/v1/clientes", json={"nombre": "Persistente", "correo": "persiste@example.test"}
        )

    # Una instancia nueva (equivalente a reiniciar el proceso o un nuevo isolate de Workers).
    transport = httpx.ASGITransport(app=create_app(settings_for(db_params)))
    async with httpx.AsyncClient(transport=transport, base_url="http://b") as second:
        response = await second.get("/api/v1/clientes")

    assert [c["correo"] for c in response.json()["items"]] == ["persiste@example.test"]


async def test_restriccion_unica_de_mysql_produce_409(client: httpx.AsyncClient) -> None:
    payload = {"nombre": "Duplicado", "correo": "dup@example.test"}

    assert (await client.post("/api/v1/clientes", json=payload)).status_code == 201
    response = await client.post("/api/v1/clientes", json=payload)

    assert response.status_code == 409
    assert response.json()["error"]["codigo"] == "correo_duplicado"


async def test_error_en_transaccion_no_deja_datos_parciales(
    client: httpx.AsyncClient, db_conn: pymysql.connections.Connection
) -> None:
    payload = {"nombre": "Único", "correo": "rollback@example.test"}
    await client.post("/api/v1/clientes", json=payload)
    await client.post("/api/v1/clientes", json=payload)

    with db_conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM clientes WHERE correo = %s", (payload["correo"],))
        assert cursor.fetchone()[0] == 1


def test_migraciones_son_idempotentes(db_params: ConnectionParams) -> None:
    with db_params.connect() as conn:
        assert apply_migrations(conn) == []
