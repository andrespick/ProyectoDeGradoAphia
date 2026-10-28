from __future__ import annotations

import httpx
import pymysql
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.anyio]

RUTA = "/api/v1/inmuebles"
PERSONA = {
    "nombre": "Laura Dueña",
    "tipo_identificacion": "CC",
    "identificacion": "1020304050",
    "telefono": "3001234567",
    "correo": "laura@example.test",
    "papeles": ["arrendatario"],
}


def _count(conn: pymysql.connections.Connection, sql: str, params: tuple[object, ...] = ()) -> int:
    conn.commit()  # nueva instantánea (REPEATABLE READ)
    with conn.cursor() as cursor:
        cursor.execute(sql, params)
        return int(cursor.fetchone()[0])


async def _persona(client: httpx.AsyncClient, **cambios: object) -> int:
    response = await client.post("/api/v1/clientes", json={**PERSONA, **cambios})
    assert response.status_code == 201
    return int(response.json()["id"])


async def test_crear_persiste_ciudad_propietarios_y_servicios(
    client: httpx.AsyncClient, db_conn: pymysql.connections.Connection
) -> None:
    person_id = await _persona(client)

    response = await client.post(
        RUTA,
        json={
            "direccion": "Calle 93B # 11A-44",
            "ciudad": "Bogotá",
            "matricula": "50C-1",
            "canon": "1500000.00",
            "estado": "DISPONIBLE",
            "servicios": [
                {"tipo": "ENERGIA", "proveedor": "Enel Ficticia", "numero_contrato": "E-1"}
            ],
            "propietarios_ids": [person_id],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["ciudad"] == "Bogotá" and body["moneda"] == "COP" and body["canon"] == "1500000.00"
    assert body["servicios"][0]["proveedor"] == "Enel Ficticia"
    assert _count(db_conn, "SELECT COUNT(*) FROM city WHERE name = 'Bogotá'") == 1
    assert (
        _count(db_conn, "SELECT COUNT(*) FROM service_provider WHERE name = 'Enel Ficticia'") == 1
    )
    assert (
        _count(db_conn, "SELECT COUNT(*) FROM property_owner WHERE person_id = %s", (person_id,))
        == 1
    )
    # La persona recibe el papel de propietario y aparece en la lista de propietarios.
    propietarios = await client.get("/api/v1/propietarios")
    assert [p["id"] for p in propietarios.json()["items"]] == [person_id]
    assert propietarios.json()["items"][0]["papeles"] == ["propietario", "arrendatario"]
    assert propietarios.json()["items"][0]["total_inmuebles"] == 1

    # Misma ciudad escrita igual: una sola fila; otra grafía crea otra (nombre exacto).
    await client.post(
        RUTA, json={"direccion": "Otra 1", "ciudad": "Bogotá", "propietarios_ids": [person_id]}
    )
    await client.post(
        RUTA, json={"direccion": "Otra 2", "ciudad": "bogotá", "propietarios_ids": [person_id]}
    )
    assert (
        _count(
            db_conn, "SELECT COUNT(*) FROM city WHERE name COLLATE utf8mb4_0900_ai_ci = 'bogota'"
        )
        == 2
    )


async def test_sin_canon_guarda_nulos_y_cumple_el_check(
    client: httpx.AsyncClient, db_conn: pymysql.connections.Connection
) -> None:
    person_id = await _persona(client)

    response = await client.post(
        RUTA, json={"direccion": "Sin canon 1", "propietarios_ids": [person_id]}
    )

    assert response.status_code == 201
    db_conn.commit()
    with db_conn.cursor() as cursor:
        cursor.execute(
            "SELECT rental_value, currency_code FROM property WHERE property_id = %s",
            (response.json()["id"],),
        )
        assert cursor.fetchone() == (None, None)


async def test_filtros_sobre_mysql(client: httpx.AsyncClient) -> None:
    dueno = await _persona(client)
    otro = await _persona(client, identificacion="999", correo="otro@example.test")
    await client.post(
        RUTA,
        json={
            "direccion": "Calle Uno",
            "ciudad": "Medellín",
            "estado": "OCUPADO",
            "propietarios_ids": [dueno],
        },
    )
    await client.post(
        RUTA,
        json={
            "direccion": "Calle Dos",
            "ciudad": "Bogotá",
            "estado": "DISPONIBLE",
            "matricula": "M-77",
            "propietarios_ids": [otro],
        },
    )

    assert (await client.get(RUTA, params={"estado": "ocupado"})).json()["total"] == 1
    assert (await client.get(RUTA, params={"ciudad": "medellin"})).json()["total"] == 1
    assert (await client.get(RUTA, params={"propietario_id": otro})).json()["total"] == 1
    assert (await client.get(RUTA, params={"q": "m-77"})).json()["total"] == 1
    assert (await client.get(RUTA, params={"q": "calle"})).json()["total"] == 2


async def test_actualizar_y_eliminar_bloqueado_por_contrato(
    client: httpx.AsyncClient, db_conn: pymysql.connections.Connection
) -> None:
    dueno = await _persona(client)
    otro = await _persona(client, identificacion="999", correo="otro@example.test")
    creado = await client.post(
        RUTA,
        json={
            "direccion": "Calle Uno",
            "servicios": [{"numero_contrato": "A"}],
            "propietarios_ids": [dueno],
        },
    )
    property_id = creado.json()["id"]

    actualizado = await client.put(
        f"{RUTA}/{property_id}",
        json={
            "direccion": "Calle Uno",
            "servicios": [{"numero_contrato": "B"}, {"numero_contrato": "C"}],
            "propietarios_ids": [otro],
        },
    )
    assert actualizado.status_code == 200
    assert [p["id"] for p in actualizado.json()["propietarios"]] == [otro]
    assert (
        _count(
            db_conn, "SELECT COUNT(*) FROM property_utility WHERE property_id = %s", (property_id,)
        )
        == 2
    )
    # Quitar al propietario del inmueble no le quita su papel.
    assert "propietario" in (await client.get(f"/api/v1/clientes/{dueno}")).json()["papeles"]

    with db_conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO property_agreement (agreement_category_id, property_id, start_date) "
            "SELECT agreement_category_id, %s, '2026-01-01' FROM agreement_category "
            "WHERE code = 'ARRENDAMIENTO'",
            (property_id,),
        )
        agreement_id = cursor.lastrowid
    db_conn.commit()
    bloqueado = await client.delete(f"{RUTA}/{property_id}")
    assert bloqueado.status_code == 409
    assert "tiene 1 contrato(s)" in bloqueado.json()["error"]["mensaje"]
    assert (await client.get(f"{RUTA}/{property_id}")).json()["total_contratos"] == 1

    with db_conn.cursor() as cursor:
        cursor.execute("DELETE FROM property_agreement WHERE agreement_id = %s", (agreement_id,))
    db_conn.commit()
    assert (await client.delete(f"{RUTA}/{property_id}")).status_code == 204
    assert (
        _count(
            db_conn, "SELECT COUNT(*) FROM property_utility WHERE property_id = %s", (property_id,)
        )
        == 0
    )
