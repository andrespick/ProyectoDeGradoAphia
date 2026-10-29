"""Migraciones 0012-0018 y funciones del Administrador de Sistemas contra MySQL real."""

from __future__ import annotations

import json

import httpx
import pymysql
import pytest

from core.fechas import hoy
from db.sql import HOY_SQL
from dbscripts import ConnectionParams
from modules.auth.passwords import hash_password
from tests.integration.conftest import crear_cuenta

pytestmark = [pytest.mark.integration, pytest.mark.anyio]

LOGIN = "/api/v1/auth/login"
CLAVE = "Clave.Segura1"
TABLAS_NUEVAS = {
    "audit_event",
    "deleted_record",
    "security_policy",
    "organization_profile",
    "backup_run",
}
PROPIETARIO = {
    "nombre": "Pedro Propietario",
    "tipo_identificacion": "CC",
    "identificacion": "55667788",
    "telefono": "3001112233",
    "correo": "pedro@example.test",
    "direccion": "Calle 1 # 2-3",
    "papeles": ["propietario"],
    "cuenta_bancaria": {"banco": "Banco Ficticio", "tipo": "ahorros", "numero": "0123456789"},
}


def _uno(conn: pymysql.connections.Connection, sql: str, params: tuple[object, ...] = ()) -> object:
    conn.commit()  # nueva instantánea (REPEATABLE READ)
    with conn.cursor() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchone()


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_tablas_nuevas_y_valores_iniciales(
    db_params: ConnectionParams, db_conn: pymysql.connections.Connection
) -> None:
    with db_conn.cursor() as cursor:
        cursor.execute(
            "SELECT table_name, table_collation FROM information_schema.tables "
            "WHERE table_schema = DATABASE()"
        )
        colaciones = dict(cursor.fetchall())
    assert {colaciones[t] for t in TABLAS_NUEVAS} == {"utf8mb4_0900_bin"}
    assert _uno(
        db_conn,
        "SELECT max_failed_attempts, lock_minutes, session_hours, min_password_length "
        "FROM security_policy",
    ) == (3, 15, 8, 8)
    assert _uno(db_conn, "SELECT legal_name FROM organization_profile") == ("APHIA S.A.S.",)
    # CHECK: una sola fila.
    with pytest.raises(pymysql.err.MySQLError), db_conn.cursor() as cursor:
        cursor.execute("INSERT INTO security_policy VALUES (2, 3, 15, 8, 8, CURRENT_TIMESTAMP(6))")
    db_conn.rollback()


async def test_login_auditado_y_sesiones_revocables(
    db_client: httpx.AsyncClient, db_conn: pymysql.connections.Connection
) -> None:
    hashed = hash_password(CLAVE, iterations=1_000)
    admin_id = crear_cuenta(db_conn, "admin.int", hashed)
    asesor_id = crear_cuenta(db_conn, "asesor.int", hashed, rol="ASESOR")

    await db_client.post(LOGIN, json={"usuario": "asesor.int", "clave": "mala"})
    admin = (await db_client.post(LOGIN, json={"usuario": "admin.int", "clave": CLAVE})).json()
    asesor = (await db_client.post(LOGIN, json={"usuario": "asesor.int", "clave": CLAVE})).json()
    assert (
        await db_client.get("/api/v1/clientes", headers=_auth(asesor["token"]))
    ).status_code == 200

    cerrar = await db_client.post(
        f"/api/v1/usuarios/{asesor_id}/cerrar-sesiones", headers=_auth(admin["token"])
    )

    assert cerrar.status_code == 204
    assert (
        await db_client.get("/api/v1/clientes", headers=_auth(asesor["token"]))
    ).status_code == 401
    assert _uno(
        db_conn, "SELECT session_version FROM user_account WHERE account_id = %s", (asesor_id,)
    ) == (1,)
    eventos = (await db_client.get("/api/v1/auditoria", headers=_auth(admin["token"]))).json()
    assert [(e["accion"], e["actor_usuario"]) for e in eventos["items"]] == [
        ("cerrar_sesiones", "admin.int"),
        ("inicio_sesion", "asesor.int"),
        ("inicio_sesion", "admin.int"),
        ("inicio_sesion_fallido", "asesor.int"),
    ]
    assert eventos["items"][0]["entidad_id"] == asesor_id
    assert eventos["items"][0]["actor_id"] == admin_id


async def test_restablecer_y_cambiar_clave(
    db_client: httpx.AsyncClient, db_conn: pymysql.connections.Connection
) -> None:
    hashed = hash_password(CLAVE, iterations=1_000)
    crear_cuenta(db_conn, "admin.int", hashed)
    asesor_id = crear_cuenta(db_conn, "asesor.int", hashed, rol="ASESOR")
    admin = (await db_client.post(LOGIN, json={"usuario": "admin.int", "clave": CLAVE})).json()

    temporal = (
        await db_client.post(
            f"/api/v1/usuarios/{asesor_id}/restablecer-clave", headers=_auth(admin["token"])
        )
    ).json()["clave_temporal"]
    sesion = (await db_client.post(LOGIN, json={"usuario": "asesor.int", "clave": temporal})).json()
    bloqueado = await db_client.get("/api/v1/clientes", headers=_auth(sesion["token"]))
    cambio = await db_client.post(
        "/api/v1/auth/cambiar-clave",
        json={"clave_actual": temporal, "clave_nueva": "Nueva.Clave22"},
        headers=_auth(sesion["token"]),
    )

    assert sesion["principal"]["debe_cambiar_clave"] is True
    assert bloqueado.status_code == 403
    assert cambio.status_code == 200
    assert (
        await db_client.get("/api/v1/clientes", headers=_auth(cambio.json()["token"]))
    ).status_code == 200
    assert _uno(
        db_conn,
        "SELECT must_change_password, session_version FROM user_account WHERE account_id = %s",
        (asesor_id,),
    ) == (0, 2)


async def test_papelera_guarda_en_la_misma_transaccion_y_restaura(
    client: httpx.AsyncClient, db_conn: pymysql.connections.Connection
) -> None:
    person_id = (await client.post("/api/v1/propietarios", json=PROPIETARIO)).json()["id"]

    assert (await client.delete(f"/api/v1/propietarios/{person_id}")).status_code == 204
    fila = _uno(
        db_conn,
        "SELECT deleted_record_id, entity_type, entity_id, label, payload FROM deleted_record",
    )
    assert fila[1:4] == ("persona", person_id, "Pedro Propietario (CC 55667788)")
    assert json.loads(fila[4])["cuenta_bancaria"]["numero"] == "0123456789"
    assert _uno(db_conn, "SELECT COUNT(*) FROM person WHERE person_id = %s", (person_id,)) == (0,)

    restaurado = await client.post(f"/api/v1/papelera/{fila[0]}/restaurar")

    assert restaurado.status_code == 200
    assert restaurado.json()["id"] != person_id
    assert _uno(db_conn, "SELECT COUNT(*) FROM deleted_record") == (0,)
    assert _uno(
        db_conn,
        "SELECT COUNT(*) FROM person_document WHERE document_identifier = '55667788'",
    ) == (1,)


async def test_borrado_rechazado_no_deja_nada_en_la_papelera(
    client: httpx.AsyncClient, db_conn: pymysql.connections.Connection
) -> None:
    person_id = (await client.post("/api/v1/propietarios", json=PROPIETARIO)).json()["id"]
    await client.post(
        "/api/v1/inmuebles", json={"direccion": "Calle 2 # 3-4", "propietarios_ids": [person_id]}
    )

    response = await client.delete(f"/api/v1/propietarios/{person_id}")

    assert response.status_code == 409
    assert _uno(db_conn, "SELECT COUNT(*) FROM deleted_record") == (0,)


async def test_catalogos_y_empresa(
    client: httpx.AsyncClient, db_conn: pymysql.connections.Connection
) -> None:
    creada = await client.post("/api/v1/catalogos/ciudades", json={"nombre": "Ciudad Ficticia"})
    city_id = creada.json()["id"]
    empresa = await client.put(
        "/api/v1/configuracion/empresa",
        json={"nombre": "Inmobiliaria Ficticia", "ciudad": "Ciudad Ficticia"},
    )
    en_uso = await client.delete(f"/api/v1/catalogos/ciudades/{city_id}")
    renombrada = await client.put(
        f"/api/v1/catalogos/ciudades/{city_id}", json={"nombre": "Ciudad Renombrada"}
    )
    cc = next(
        i
        for i in (await client.get("/api/v1/catalogos/tipos-identificacion")).json()
        if i["codigo"] == "CC"
    )

    assert creada.status_code == 201
    assert empresa.json()["ciudad"] == "Ciudad Ficticia"
    assert _uno(db_conn, "SELECT city_id FROM organization_profile") == (city_id,)
    assert en_uso.status_code == 409
    assert renombrada.json()["nombre"] == "Ciudad Renombrada"
    assert (await client.get("/api/v1/configuracion/empresa")).json()[
        "ciudad"
    ] == "Ciudad Renombrada"
    assert cc["nombre"] == "Cédula de ciudadanía"

    nuevo = await client.post(
        "/api/v1/catalogos/tipos-contrato", json={"codigo": "comodato", "nombre": "Comodato"}
    )
    duplicado = await client.post(
        "/api/v1/catalogos/tipos-contrato", json={"codigo": "COMODATO", "nombre": "Otro"}
    )
    borrado = await client.delete(f"/api/v1/catalogos/tipos-contrato/{nuevo.json()['id']}")
    assert nuevo.json()["codigo"] == "COMODATO"
    assert duplicado.status_code == 409
    assert borrado.status_code == 204


async def test_estado_del_sistema_y_solicitud_de_respaldo(
    client: httpx.AsyncClient, db_conn: pymysql.connections.Connection
) -> None:
    primera = await client.post("/api/v1/sistema/respaldos")
    segunda = await client.post("/api/v1/sistema/respaldos")
    estado = (await client.get("/api/v1/sistema/estado")).json()

    assert primera.status_code == 202
    assert segunda.status_code == 409
    assert _uno(db_conn, "SELECT trigger_type, status FROM backup_run") == ("MANUAL", "SOLICITADO")
    assert estado["base_de_datos"]["disponible"] is True
    assert estado["base_de_datos"]["version"].startswith("8.")
    assert estado["migraciones"]["ultima"] == "0018"
    assert estado["migraciones"]["aplicadas"] >= 18
    assert estado["respaldos"]["pendiente"]["estado"] == "solicitado"
    assert estado["respaldos"]["atrasado"] is True


async def test_politica_persistida_se_aplica_al_login(
    db_client: httpx.AsyncClient, db_conn: pymysql.connections.Connection
) -> None:
    hashed = hash_password(CLAVE, iterations=1_000)
    crear_cuenta(db_conn, "admin.int", hashed)
    crear_cuenta(db_conn, "asesor.int", hashed, rol="ASESOR")
    admin = (await db_client.post(LOGIN, json={"usuario": "admin.int", "clave": CLAVE})).json()
    await db_client.put(
        "/api/v1/configuracion/seguridad",
        json={"max_intentos": 4, "minutos_bloqueo": 20, "horas_sesion": 8, "largo_minimo_clave": 8},
        headers=_auth(admin["token"]),
    )

    codigos = [
        (await db_client.post(LOGIN, json={"usuario": "asesor.int", "clave": "mala"})).status_code
        for _ in range(4)
    ]

    assert codigos == [401, 401, 401, 423]
    assert _uno(
        db_conn,
        "SELECT TIMESTAMPDIFF(MINUTE, UTC_TIMESTAMP(6), locked_until) FROM user_account "
        "WHERE user_name = 'asesor.int'",
    )[0] in (19, 20)


def test_hoy_en_sql_coincide_con_hoy_en_python(db_conn: pymysql.connections.Connection) -> None:
    # Los estados de contrato se calculan en SQL (filtros, resumen) y en Python (listado).
    assert _uno(db_conn, f"SELECT {HOY_SQL}") == (hoy(),)
