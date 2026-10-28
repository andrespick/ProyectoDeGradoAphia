# ruff: noqa: S608 - nombres de tabla fijos en las comprobaciones
from __future__ import annotations

import httpx
import pymysql
import pytest

from dbscripts import ConnectionParams
from main import create_app
from migrate import apply_migrations
from tests.integration.conftest import settings_for

pytestmark = [pytest.mark.integration, pytest.mark.anyio]

PERSONA = {
    "nombre": "Ana García",
    "tipo_identificacion": "CC",
    "identificacion": "1020304050",
    "telefono": "3001234567",
    "correo": "ana@example.test",
    "direccion": "Calle 1 # 2-3",
    "papeles": ["propietario"],
    "cuenta_bancaria": {"banco": "Banco Ficticio", "tipo": "AHORROS", "numero": "0123456789"},
}


def _count(conn: pymysql.connections.Connection, sql: str, params: tuple[object, ...] = ()) -> int:
    conn.commit()  # nueva instantánea (REPEATABLE READ)
    with conn.cursor() as cursor:
        cursor.execute(sql, params)
        return int(cursor.fetchone()[0])


async def test_ready_con_mysql_real(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/ready")

    assert response.status_code == 200
    assert response.json()["checks"]["database"] == "ok"


async def test_crear_persiste_en_todas_las_tablas_hijas(
    client: httpx.AsyncClient, db_conn: pymysql.connections.Connection
) -> None:
    response = await client.post("/api/v1/propietarios", json=PERSONA)

    assert response.status_code == 201
    person_id = response.json()["id"]
    for tabla in (
        "person_document",
        "person_phone",
        "person_email",
        "person_party_role",
        "bank_account",
    ):
        assert (
            _count(db_conn, f"SELECT COUNT(*) FROM {tabla} WHERE person_id = %s", (person_id,)) == 1
        )
    assert (
        _count(db_conn, "SELECT COUNT(*) FROM financial_institution WHERE name = 'Banco Ficticio'")
        == 1
    )

    # El mismo banco escrito igual no se duplica; otra persona, otra cuenta.
    otra = await client.post(
        "/api/v1/propietarios",
        json={**PERSONA, "identificacion": "555", "correo": "otra@example.test"},
    )
    assert otra.status_code == 201
    assert (
        _count(db_conn, "SELECT COUNT(*) FROM financial_institution WHERE name = 'Banco Ficticio'")
        == 1
    )


async def test_filtro_q_ignora_mayusculas_y_acentos(client: httpx.AsyncClient) -> None:
    await client.post("/api/v1/clientes", json={**PERSONA, "papeles": ["arrendatario"]})

    por_nombre = await client.get("/api/v1/clientes?q=garcia")
    por_identificacion = await client.get("/api/v1/clientes?q=10203")
    por_correo = await client.get("/api/v1/propietarios?correo=ANA@")

    assert por_nombre.json()["total"] == 1
    assert por_identificacion.json()["total"] == 1
    assert por_correo.json()["total"] == 0  # no es propietaria
    assert (await client.get("/api/v1/clientes?correo=ANA@")).json()["total"] == 1


async def test_identificacion_duplicada_no_deja_filas_parciales(
    client: httpx.AsyncClient, db_conn: pymysql.connections.Connection
) -> None:
    assert (await client.post("/api/v1/clientes", json=PERSONA)).status_code == 201

    response = await client.post("/api/v1/clientes", json={**PERSONA, "nombre": "Otra Persona"})

    assert response.status_code == 409
    assert response.json()["error"]["codigo"] == "identificacion_duplicada"
    assert _count(db_conn, "SELECT COUNT(*) FROM person") == 1
    assert _count(db_conn, "SELECT COUNT(*) FROM person_phone") == 1


async def test_actualizar_reemplaza_contacto_y_papeles(
    client: httpx.AsyncClient, db_conn: pymysql.connections.Connection
) -> None:
    person_id = (await client.post("/api/v1/clientes", json=PERSONA)).json()["id"]

    response = await client.put(
        f"/api/v1/clientes/{person_id}",
        json={
            **PERSONA,
            "telefono": "3109876543",
            "correo": "nueva@example.test",
            "papeles": ["propietario", "codeudor"],
            "cuenta_bancaria": None,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["telefono"] == "3109876543"
    assert body["papeles"] == ["propietario", "codeudor"]
    assert body["cuenta_bancaria"] is None
    assert (
        _count(db_conn, "SELECT COUNT(*) FROM person_phone WHERE person_id = %s", (person_id,)) == 1
    )
    assert (
        _count(db_conn, "SELECT COUNT(*) FROM person_email WHERE person_id = %s", (person_id,)) == 1
    )
    assert (
        _count(db_conn, "SELECT COUNT(*) FROM person_party_role WHERE person_id = %s", (person_id,))
        == 2
    )
    assert (
        _count(db_conn, "SELECT COUNT(*) FROM bank_account WHERE person_id = %s", (person_id,)) == 0
    )
    assert (await client.get("/api/v1/codeudores")).json()["total"] == 1


async def test_eliminar_borra_hijas_y_bloquea_si_tiene_inmueble(
    client: httpx.AsyncClient, db_conn: pymysql.connections.Connection
) -> None:
    person_id = (await client.post("/api/v1/propietarios", json=PERSONA)).json()["id"]
    with db_conn.cursor() as cursor:
        cursor.execute("INSERT INTO property (address) VALUES ('Inmueble ficticio')")
        property_id = cursor.lastrowid
        cursor.execute("INSERT INTO property_owner VALUES (%s, %s)", (property_id, person_id))
    db_conn.commit()

    bloqueado = await client.delete(f"/api/v1/propietarios/{person_id}")
    assert bloqueado.status_code == 409
    assert "propietaria de 1 inmueble(s)" in bloqueado.json()["error"]["mensaje"]
    detalle = await client.get(f"/api/v1/propietarios/{person_id}")
    assert detalle.json()["inmuebles"][0]["direccion"] == "Inmueble ficticio"
    assert detalle.json()["total_inmuebles"] == 1

    with db_conn.cursor() as cursor:
        cursor.execute("DELETE FROM property_owner WHERE person_id = %s", (person_id,))
        cursor.execute("DELETE FROM property WHERE property_id = %s", (property_id,))
    db_conn.commit()
    assert (await client.delete(f"/api/v1/propietarios/{person_id}")).status_code == 204
    assert _count(db_conn, "SELECT COUNT(*) FROM person") == 0
    assert _count(db_conn, "SELECT COUNT(*) FROM bank_account") == 0


async def test_buscar_es_exacto(client: httpx.AsyncClient) -> None:
    await client.post("/api/v1/clientes", json={**PERSONA, "identificacion": "ABC-123"})

    exacta = await client.get(
        "/api/v1/personas/buscar", params={"tipo_identificacion": "CC", "identificacion": "ABC-123"}
    )
    minusculas = await client.get(
        "/api/v1/personas/buscar", params={"tipo_identificacion": "CC", "identificacion": "abc-123"}
    )

    assert exacta.status_code == 200
    assert minusculas.status_code == 404


async def test_datos_persisten_entre_instancias_de_la_api(
    db_params: ConnectionParams, db_conn: pymysql.connections.Connection
) -> None:
    transport = httpx.ASGITransport(app=create_app(settings_for(db_params)))
    async with httpx.AsyncClient(transport=transport, base_url="http://a") as first:
        await first.post("/api/v1/clientes", json=PERSONA)

    # Una instancia nueva (equivalente a reiniciar el proceso o un nuevo isolate de Workers).
    transport = httpx.ASGITransport(app=create_app(settings_for(db_params)))
    async with httpx.AsyncClient(transport=transport, base_url="http://b") as second:
        response = await second.get("/api/v1/clientes")

    assert [p["identificacion"] for p in response.json()["items"]] == ["1020304050"]


def test_migraciones_son_idempotentes(db_params: ConnectionParams) -> None:
    with db_params.connect() as conn:
        assert apply_migrations(conn) == []
