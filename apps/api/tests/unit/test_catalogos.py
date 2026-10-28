from __future__ import annotations

import httpx
import pytest

from main import create_app
from tests.conftest import make_settings

pytestmark = pytest.mark.anyio


async def test_devuelve_todos_los_catalogos(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/catalogos")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "tipos_identificacion",
        "papeles",
        "roles",
        "estados_ocupacion",
        "tipos_contrato",
        "tipos_cuenta_bancaria",
        "tipos_servicio",
        "monedas",
        "ciudades",
        "bancos",
        "proveedores_servicios",
    }
    assert [p["codigo"] for p in body["papeles"]] == ["propietario", "arrendatario", "codeudor"]
    assert [r["codigo"] for r in body["roles"]] == ["admin_sistemas", "administrativo", "asesor"]
    assert body["ciudades"] == [{"id": 9001, "nombre": "Bogotá"}]


async def test_requiere_autenticacion() -> None:
    app = create_app(make_settings(auth_mode="disabled"))

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.get("/api/v1/catalogos")

    assert response.status_code == 401
