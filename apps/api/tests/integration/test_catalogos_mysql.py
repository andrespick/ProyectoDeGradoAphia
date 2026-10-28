from __future__ import annotations

import httpx
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.anyio]


async def test_catalogos_desde_mysql(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/catalogos")

    assert response.status_code == 200
    body = response.json()
    assert {o["codigo"] for o in body["tipos_identificacion"]} == {"CC", "CE", "NIT", "PAS", "TI"}
    assert [o["codigo"] for o in body["papeles"]] == ["propietario", "arrendatario", "codeudor"]
    assert [o["codigo"] for o in body["roles"]] == ["admin_sistemas", "administrativo", "asesor"]
    assert [o["codigo"] for o in body["estados_ocupacion"]] == ["DISPONIBLE", "OCUPADO"]
    assert body["monedas"] == [{"codigo": "COP", "nombre": "Peso colombiano"}]
    servicios = {o["codigo"] for o in body["tipos_servicio"]}
    assert servicios == {"AGUA", "ENERGIA", "GAS", "INTERNET", "ASEO"}
    # La base de pruebas no carga seeds: los catálogos de nombre libre empiezan vacíos.
    assert body["ciudades"] == []
    assert body["bancos"] == []
    assert body["proveedores_servicios"] == []
