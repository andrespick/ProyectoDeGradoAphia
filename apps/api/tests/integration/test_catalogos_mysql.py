from __future__ import annotations

import asyncio

import httpx
import pymysql
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


async def test_altas_simultaneas_no_se_bloquean_ni_duplican_bancos_y_proveedores(
    client: httpx.AsyncClient, db_conn: pymysql.connections.Connection
) -> None:
    def persona(i: int) -> dict[str, object]:
        cuenta = {"banco": "Banco Nuevo", "tipo": "ahorros", "numero": f"00{i}"}
        return {
            "nombre": f"Dueño {i}",
            "tipo_identificacion": "CC",
            "identificacion": f"7000{i}",
            "papeles": ["propietario"],
            "cuenta_bancaria": cuenta,
        }

    personas = await asyncio.gather(
        *(client.post("/api/v1/propietarios", json=persona(i)) for i in range(5))
    )
    assert [r.status_code for r in personas] == [201] * 5
    # Cada respuesta ve el banco aunque lo haya creado otra solicitud simultánea.
    assert {r.json()["cuenta_bancaria"]["banco"] for r in personas} == {"Banco Nuevo"}
    servicio = {"tipo": "AGUA", "proveedor": "Acueducto Nuevo", "numero_contrato": "1"}
    inmuebles = await asyncio.gather(
        *(
            client.post(
                "/api/v1/inmuebles",
                json={
                    "direccion": f"Calle {i}",
                    "propietarios_ids": [personas[0].json()["id"]],
                    "servicios": [servicio],
                },
            )
            for i in range(5)
        )
    )
    assert [r.status_code for r in inmuebles] == [201] * 5
    assert {r.json()["servicios"][0]["proveedor"] for r in inmuebles} == {"Acueducto Nuevo"}

    db_conn.commit()  # nueva instantánea (REPEATABLE READ)
    with db_conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM financial_institution WHERE name = 'Banco Nuevo'")
        assert cursor.fetchone() == (1,)
        cursor.execute("SELECT COUNT(*) FROM service_provider WHERE name = 'Acueducto Nuevo'")
        assert cursor.fetchone() == (1,)
        with pytest.raises(pymysql.err.IntegrityError):
            cursor.execute("INSERT INTO financial_institution (name) VALUES ('Banco Nuevo')")
