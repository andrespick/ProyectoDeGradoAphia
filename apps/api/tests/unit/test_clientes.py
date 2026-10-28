from __future__ import annotations

import httpx
import pytest

from tests.conftest import InMemoryClientesRepository

pytestmark = pytest.mark.anyio

CLIENTE_VALIDO = {"nombre": "Cliente Ficticio Uno", "correo": "Cliente.Uno@Example.test"}


async def test_crear_y_listar_cliente(
    client: httpx.AsyncClient, repository: InMemoryClientesRepository
) -> None:
    created = await client.post("/api/v1/clientes", json=CLIENTE_VALIDO)

    assert created.status_code == 201
    body = created.json()
    assert body["id"] == 1
    assert body["nombre"] == "Cliente Ficticio Uno"
    assert body["correo"] == "cliente.uno@example.test"  # normalizado a minúsculas
    assert {"creado_en", "actualizado_en"} <= body.keys()

    listed = await client.get("/api/v1/clientes")

    assert listed.status_code == 200
    page = listed.json()
    assert page["total"] == 1
    assert page["limit"] == 20
    assert page["offset"] == 0
    assert [c["correo"] for c in page["items"]] == ["cliente.uno@example.test"]


async def test_nombre_se_normaliza_espacios(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/clientes", json={"nombre": "  Ana    María  ", "correo": "ana@example.test"}
    )

    assert response.status_code == 201
    assert response.json()["nombre"] == "Ana María"


@pytest.mark.parametrize(
    ("payload", "campo"),
    [
        ({"nombre": "Cliente", "correo": "no-es-un-correo"}, "correo"),
        ({"nombre": "Cliente", "correo": "falta@dominio"}, "correo"),
        ({"nombre": "C", "correo": "corto@example.test"}, "nombre"),
        ({"nombre": "x" * 151, "correo": "largo@example.test"}, "nombre"),
        ({"nombre": "Con\x00control", "correo": "ctrl@example.test"}, "nombre"),
        ({"correo": "sin-nombre@example.test"}, "nombre"),
        ({"nombre": "Cliente Valido", "correo": "extra@example.test", "rol": "admin"}, "rol"),
    ],
)
async def test_validacion_de_entradas(
    client: httpx.AsyncClient, payload: dict[str, str], campo: str
) -> None:
    response = await client.post("/api/v1/clientes", json=payload)

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["codigo"] == "validacion"
    assert campo in {d["campo"] for d in error["detalles"]}
    # La respuesta no refleja los valores enviados.
    for value in payload.values():
        if len(value) > 3:
            assert value not in response.text


async def test_cuerpo_que_no_es_json_responde_422(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/clientes", content=b"nombre=x", headers={"content-type": "text/plain"}
    )

    assert response.status_code == 422


async def test_correo_duplicado_responde_409(client: httpx.AsyncClient) -> None:
    first = await client.post("/api/v1/clientes", json=CLIENTE_VALIDO)
    second = await client.post(
        "/api/v1/clientes", json={**CLIENTE_VALIDO, "correo": "CLIENTE.UNO@example.test"}
    )

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["error"]["codigo"] == "correo_duplicado"


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1", "limit=abc"])
async def test_paginacion_invalida_responde_422(client: httpx.AsyncClient, query: str) -> None:
    response = await client.get(f"/api/v1/clientes?{query}")

    assert response.status_code == 422


async def test_paginacion(client: httpx.AsyncClient) -> None:
    for i in range(3):
        await client.post(
            "/api/v1/clientes", json={"nombre": f"Cliente {i}", "correo": f"c{i}@example.test"}
        )

    response = await client.get("/api/v1/clientes?limit=2&offset=1")

    page = response.json()
    assert page["total"] == 3
    assert [c["correo"] for c in page["items"]] == ["c1@example.test", "c0@example.test"]
