from __future__ import annotations

from datetime import date, timedelta

import httpx
import pymysql
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.anyio]

RUTA = "/api/v1/contratos"
PERSONA = {
    "nombre": "Laura Dueña",
    "tipo_identificacion": "CC",
    "identificacion": "1020304050",
    "telefono": "3001234567",
    "correo": "laura@example.test",
    "papeles": ["propietario"],
}


def _count(conn: pymysql.connections.Connection, sql: str, params: tuple[object, ...] = ()) -> int:
    conn.commit()  # nueva instantánea (REPEATABLE READ)
    with conn.cursor() as cursor:
        cursor.execute(sql, params)
        return int(cursor.fetchone()[0])


async def _persona(client: httpx.AsyncClient, identificacion: str, nombre: str) -> int:
    response = await client.post(
        "/api/v1/clientes",
        json={
            **PERSONA,
            "identificacion": identificacion,
            "nombre": nombre,
            "correo": f"{identificacion}@example.test",
            "papeles": ["arrendatario"],
        },
    )
    assert response.status_code == 201
    return int(response.json()["id"])


async def _escenario(client: httpx.AsyncClient) -> dict[str, int]:
    dueno = await _persona(client, "1001", "Laura Dueña")
    inquilino = await _persona(client, "1002", "Carlos Inquilino")
    fiador = await _persona(client, "1003", "Pedro Fiador")
    fiadora = await _persona(client, "1004", "Sofía Fiadora")
    inmueble = await client.post(
        "/api/v1/inmuebles",
        json={"direccion": "Calle 93B # 11A-44", "ciudad": "Bogotá", "propietarios_ids": [dueno]},
    )
    assert inmueble.status_code == 201
    return {
        "dueno": dueno,
        "inquilino": inquilino,
        "fiador": fiador,
        "fiadora": fiadora,
        "inmueble": int(inmueble.json()["id"]),
    }


def _nuevo(ids: dict[str, int], **cambios: object) -> dict[str, object]:
    return {
        "tipo": "ARRENDAMIENTO",
        "inmueble_id": ids["inmueble"],
        "fecha_inicio": "2026-01-01",
        "fecha_fin": "2026-12-31",
        "canon_pactado": "1500000.00",
        "condiciones": "Pago mensual anticipado.",
        "texto": "CONTRATO DE ARRENDAMIENTO\nTexto ficticio.",
        "arrendatario_id": ids["inquilino"],
        "codeudores_ids": [ids["fiador"], ids["fiadora"]],
        **cambios,
    }


async def test_crear_persiste_partes_con_sus_codigos_y_papeles_automaticos(
    client: httpx.AsyncClient, db_conn: pymysql.connections.Connection
) -> None:
    ids = await _escenario(client)

    response = await client.post(RUTA, json=_nuevo(ids))

    assert response.status_code == 201
    body = response.json()
    assert body["moneda"] == "COP" and body["canon_pactado"] == "1500000.00"
    assert [p["id"] for p in body["propietarios"]] == [ids["dueno"]]  # tomados de property_owner
    assert body["arrendatario"]["id"] == ids["inquilino"]
    partes = "SELECT COUNT(*) FROM agreement_party ap JOIN party_role pr USING (party_role_id) "
    assert _count(db_conn, partes + "WHERE pr.code = 'OWNER'") == 1
    assert _count(db_conn, partes + "WHERE pr.code = 'TENANT'") == 1
    assert _count(db_conn, partes + "WHERE pr.code = 'CO_DEBTOR'") == 2
    # Papeles automáticos: los fiadores aparecen en /codeudores?contrato_id= y volver a
    # guardar no duplica el papel.
    codeudores = await client.get("/api/v1/codeudores", params={"contrato_id": body["id"]})
    assert sorted(c["id"] for c in codeudores.json()["items"]) == sorted(
        [ids["fiador"], ids["fiadora"]]
    )
    assert (await client.put(f"{RUTA}/{body['id']}", json=_nuevo(ids))).status_code == 200
    assert (
        _count(
            db_conn,
            "SELECT COUNT(*) FROM person_party_role ppr JOIN party_role pr USING (party_role_id) "
            "WHERE ppr.person_id = %s AND pr.code = 'CO_DEBTOR'",
            (ids["fiador"],),
        )
        == 1
    )
    detalle = await client.get(f"/api/v1/clientes/{ids['fiador']}")
    assert [c["id"] for c in detalle.json()["contratos_como_codeudor"]] == [body["id"]]
    assert detalle.json()["contratos_como_arrendatario"] == []


async def test_filtros_por_fechas_estado_y_texto_sobre_mysql(client: httpx.AsyncClient) -> None:
    ids = await _escenario(client)
    hoy = date.today()
    a = await client.post(
        RUTA, json=_nuevo(ids, fecha_inicio="2025-01-01", fecha_fin="2025-06-30", codeudores_ids=[])
    )
    b = await client.post(
        RUTA,
        json=_nuevo(
            ids,
            tipo="ADMINISTRACION",
            fecha_inicio=str(hoy - timedelta(days=30)),
            fecha_fin=str(hoy + timedelta(days=20)),
            canon_pactado=None,
            arrendatario_id=None,
        ),
    )
    assert a.status_code == b.status_code == 201
    ids_a, ids_b = a.json()["id"], b.json()["id"]

    async def listar(**params: object) -> list[int]:
        response = await client.get(RUTA, params=params)
        assert response.status_code == 200, response.text
        return [c["id"] for c in response.json()["items"]]

    assert await listar(fecha_desde="2025-07-01") == [ids_b]
    assert await listar(fecha_hasta="2025-01-01") == [ids_a]
    assert await listar(fecha_desde="2025-06-30", fecha_hasta=str(hoy)) == [ids_b, ids_a]
    assert await listar(estado="vigente") == [ids_b]
    assert await listar(estado="por_vencer") == [ids_b]
    assert await listar(estado="finalizado") == [ids_a]
    assert await listar(inquilino_id=ids["inquilino"]) == [ids_a]
    assert await listar(tipo="administracion") == [ids_b]
    assert await listar(q="FIADOR") == [ids_b]  # la fiadora sigue en B; A no tiene codeudores
    assert await listar(q="calle 93b") == [ids_b, ids_a]
    assert b.json()["moneda"] is None and b.json()["arrendatario"] is None


async def test_eliminar_bloqueado_por_registro_financiero(
    client: httpx.AsyncClient, db_conn: pymysql.connections.Connection
) -> None:
    ids = await _escenario(client)
    creado = await client.post(RUTA, json=_nuevo(ids))
    agreement_id = creado.json()["id"]
    with db_conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO financial_category (code, name) VALUES ('CANON_TEST', 'Canon') "
            "ON DUPLICATE KEY UPDATE name = name"
        )
        cursor.execute(
            "INSERT INTO payment_state (code, name) VALUES ('PAGADO_TEST', 'Pagado') "
            "ON DUPLICATE KEY UPDATE name = name"
        )
        cursor.execute(
            "INSERT INTO financial_record (agreement_id, financial_category_id, amount, "
            "record_date, payment_state_id, currency_code) SELECT %s, fc.financial_category_id, "
            "1500000.00, '2026-02-01', ps.payment_state_id, 'COP' FROM financial_category fc, "
            "payment_state ps WHERE fc.code = 'CANON_TEST' AND ps.code = 'PAGADO_TEST'",
            (agreement_id,),
        )
    db_conn.commit()

    bloqueado = await client.delete(f"{RUTA}/{agreement_id}")
    assert bloqueado.status_code == 409
    assert bloqueado.json()["error"]["codigo"] == "contrato_con_dependencias"

    with db_conn.cursor() as cursor:
        cursor.execute("DELETE FROM financial_record WHERE agreement_id = %s", (agreement_id,))
    db_conn.commit()
    assert (await client.delete(f"{RUTA}/{agreement_id}")).status_code == 204
    assert _count(db_conn, "SELECT COUNT(*) FROM agreement_party") == 0


async def test_busqueda_global_sobre_mysql(client: httpx.AsyncClient) -> None:
    ids = await _escenario(client)
    await client.post(RUTA, json=_nuevo(ids))

    response = await client.get("/api/v1/buscar", params={"q": "fiador"})

    assert response.status_code == 200
    body = response.json()
    assert sorted(p["nombre"] for p in body["personas"]) == ["Pedro Fiador", "Sofía Fiadora"]
    assert body["inmuebles"] == []
    assert [c["inmueble"]["direccion"] for c in body["contratos"]] == ["Calle 93B # 11A-44"]
    calle = (await client.get("/api/v1/buscar", params={"q": "CALLE 93"})).json()
    assert len(calle["inmuebles"]) == 1 and len(calle["contratos"]) == 1
