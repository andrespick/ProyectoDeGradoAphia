from __future__ import annotations

import httpx
import pymysql
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.anyio]

RUTA = "/api/v1/usuarios"
NUEVO = {
    "usuario": "mperez",
    "nombre": "María Pérez",
    "tipo_identificacion": "CC",
    "identificacion": "1020304050",
    "correo": "maria.perez@example.test",
    "clave": "Clave.Segura1",
    "rol": "asesor",
}


def _count(conn: pymysql.connections.Connection, sql: str, params: tuple[object, ...] = ()) -> int:
    with conn.cursor() as cursor:
        cursor.execute(sql, params)
        return int(cursor.fetchone()[0])


async def test_crear_persiste_persona_documento_cuenta_y_rol(
    client: httpx.AsyncClient, db_conn: pymysql.connections.Connection
) -> None:
    response = await client.post(RUTA, json=NUEVO)

    assert response.status_code == 201
    account_id = response.json()["id"]
    assert _count(db_conn, "SELECT COUNT(*) FROM person") == 1
    assert (
        _count(
            db_conn, "SELECT COUNT(*) FROM person_document WHERE document_identifier = '1020304050'"
        )
        == 1
    )
    with db_conn.cursor() as cursor:
        cursor.execute(
            "SELECT ua.user_name, ua.login_email, ua.hashed_password, ar.code "
            "FROM user_account ua JOIN user_role ur ON ur.account_id = ua.account_id "
            "JOIN app_role ar ON ar.role_id = ur.role_id WHERE ua.account_id = %s",
            (account_id,),
        )
        user_name, login_email, hashed, rol = cursor.fetchone()
    assert (user_name, login_email, rol) == ("mperez", "maria.perez@example.test", "ASESOR")
    assert hashed.startswith("pbkdf2_sha256$") and "Clave.Segura1" not in hashed

    obtenido = await client.get(f"{RUTA}/{account_id}")
    assert obtenido.json()["identificacion"] == "1020304050"
    assert obtenido.json()["rol"] == "asesor"


async def test_una_persona_existente_reutiliza_su_fila(
    client: httpx.AsyncClient, db_conn: pymysql.connections.Connection
) -> None:
    with db_conn.cursor() as cursor:
        cursor.execute("INSERT INTO person (full_name) VALUES ('Cliente Previo')")
        person_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO person_document (person_id, document_type_id, document_identifier) "
            "SELECT %s, document_type_id, '1020304050' FROM document_type "
            "WHERE issuer_scope = 'CO' AND code = 'CC'",
            (person_id,),
        )
    db_conn.commit()

    response = await client.post(RUTA, json=NUEVO)

    assert response.status_code == 201
    assert _count(db_conn, "SELECT COUNT(*) FROM person") == 1
    assert (
        _count(db_conn, "SELECT COUNT(*) FROM user_account WHERE person_id = %s", (person_id,)) == 1
    )


async def test_actualizar_cambia_rol_identificacion_y_estado(
    client: httpx.AsyncClient, db_conn: pymysql.connections.Connection
) -> None:
    account_id = (await client.post(RUTA, json=NUEVO)).json()["id"]
    assert (
        await client.post(
            RUTA,
            json={**NUEVO, "usuario": "root", "identificacion": "1000001", "rol": "admin_sistemas"},
        )
    ).status_code == 201

    response = await client.put(
        f"{RUTA}/{account_id}",
        json={
            "nombre": "María P.",
            "tipo_identificacion": "CE",
            "identificacion": "E-55",
            "correo": "mp@example.test",
            "rol": "administrativo",
            "activo": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert (body["tipo_identificacion"], body["identificacion"]) == ("CE", "E-55")
    assert body["rol"] == "administrativo" and body["activo"] is False
    assert (
        _count(db_conn, "SELECT COUNT(*) FROM user_role WHERE account_id = %s", (account_id,)) == 1
    )
    inactivos = await client.get(RUTA, params={"estado": "inactivo"})
    assert [u["usuario"] for u in inactivos.json()["items"]] == ["mperez"]


async def test_identificacion_de_otra_persona_responde_409(client: httpx.AsyncClient) -> None:
    primero = (await client.post(RUTA, json=NUEVO)).json()["id"]
    await client.post(RUTA, json={**NUEVO, "usuario": "otro", "identificacion": "555"})

    response = await client.put(
        f"{RUTA}/{primero}",
        json={
            **{k: v for k, v in NUEVO.items() if k not in {"usuario", "clave"}},
            "identificacion": "555",
            "activo": True,
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["codigo"] == "identificacion_duplicada"


async def test_tipo_de_identificacion_inexistente_responde_422(client: httpx.AsyncClient) -> None:
    response = await client.post(RUTA, json={**NUEVO, "tipo_identificacion": "XX"})

    assert response.status_code == 422
    assert response.json()["error"]["codigo"] == "catalogo_invalido"


async def test_eliminar_conserva_la_persona(
    client: httpx.AsyncClient, db_conn: pymysql.connections.Connection
) -> None:
    account_id = (await client.post(RUTA, json=NUEVO)).json()["id"]

    assert (await client.delete(f"{RUTA}/{account_id}")).status_code == 204

    assert _count(db_conn, "SELECT COUNT(*) FROM user_account") == 0
    assert _count(db_conn, "SELECT COUNT(*) FROM person") == 1
