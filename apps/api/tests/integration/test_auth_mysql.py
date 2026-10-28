from __future__ import annotations

import httpx
import pymysql
import pytest

from modules.auth.passwords import hash_password
from tests.integration.conftest import crear_cuenta

pytestmark = [pytest.mark.integration, pytest.mark.anyio]

LOGIN = "/api/v1/auth/login"
CLAVE = "Clave.Segura1"


async def test_login_y_me_contra_mysql(
    db_client: httpx.AsyncClient, db_conn: pymysql.connections.Connection
) -> None:
    account_id = crear_cuenta(db_conn, "admin.int", hash_password(CLAVE, iterations=1_000))

    response = await db_client.post(LOGIN, json={"usuario": "admin.int", "clave": CLAVE})

    assert response.status_code == 200
    body = response.json()
    assert body["principal"]["sujeto"] == str(account_id)
    assert body["principal"]["roles"] == ["admin_sistemas"]
    me = await db_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {body['token']}"}
    )
    assert me.status_code == 200
    # El nombre de usuario distingue mayúsculas (colación binaria).
    otro = await db_client.post(LOGIN, json={"usuario": "Admin.int", "clave": CLAVE})
    assert otro.status_code == 401


async def test_tres_fallos_persisten_el_bloqueo_y_el_admin_lo_levanta(
    db_client: httpx.AsyncClient, db_conn: pymysql.connections.Connection
) -> None:
    hashed = hash_password(CLAVE, iterations=1_000)
    admin_id = crear_cuenta(db_conn, "admin.int", hashed)
    user_id = crear_cuenta(db_conn, "asesor.int", hashed, rol="ASESOR")

    for _ in range(3):
        await db_client.post(LOGIN, json={"usuario": "asesor.int", "clave": "mala"})
    bloqueada = await db_client.post(LOGIN, json={"usuario": "asesor.int", "clave": CLAVE})

    assert bloqueada.status_code == 423
    db_conn.commit()  # nueva instantánea (REPEATABLE READ)
    with db_conn.cursor() as cursor:
        cursor.execute(
            "SELECT failed_login_attempts, locked_until FROM user_account WHERE account_id = %s",
            (user_id,),
        )
        intentos, locked_until = cursor.fetchone()
    assert intentos == 3
    assert locked_until is not None

    token = (await db_client.post(LOGIN, json={"usuario": "admin.int", "clave": CLAVE})).json()[
        "token"
    ]
    headers = {"Authorization": f"Bearer {token}"}
    lista = await db_client.get("/api/v1/usuarios?estado=bloqueado", headers=headers)
    assert [u["usuario"] for u in lista.json()["items"]] == ["asesor.int"]
    assert lista.json()["items"][0]["bloqueada"] is True

    desbloqueo = await db_client.post(f"/api/v1/usuarios/{user_id}/desbloquear", headers=headers)
    assert desbloqueo.status_code == 200
    assert desbloqueo.json()["bloqueada"] is False
    db_conn.commit()
    with db_conn.cursor() as cursor:
        cursor.execute(
            "SELECT failed_login_attempts, locked_until FROM user_account WHERE account_id = %s",
            (user_id,),
        )
        assert cursor.fetchone() == (0, None)
    assert (
        await db_client.post(LOGIN, json={"usuario": "asesor.int", "clave": CLAVE})
    ).status_code == 200
    assert admin_id != user_id


async def test_login_correcto_reinicia_los_intentos(
    db_client: httpx.AsyncClient, db_conn: pymysql.connections.Connection
) -> None:
    user_id = crear_cuenta(db_conn, "ana.int", hash_password(CLAVE, iterations=1_000))

    await db_client.post(LOGIN, json={"usuario": "ana.int", "clave": "mala"})
    await db_client.post(LOGIN, json={"usuario": "ana.int", "clave": "mala"})
    ok = await db_client.post(LOGIN, json={"usuario": "ana.int", "clave": CLAVE})

    assert ok.status_code == 200
    db_conn.commit()
    with db_conn.cursor() as cursor:
        cursor.execute(
            "SELECT failed_login_attempts FROM user_account WHERE account_id = %s", (user_id,)
        )
        assert cursor.fetchone()[0] == 0
