"""Evidencia del RNF de rendimiento (< 3 s por consulta) con 500 personas; no es un benchmark."""

from __future__ import annotations

import time

import httpx
import pymysql
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.anyio]

PERSONAS = 500
LIMITE_SEGUNDOS = 3.0


def _sembrar(conn: pymysql.connections.Connection) -> None:
    with conn.cursor() as cursor:
        cursor.executemany(
            "INSERT INTO person (person_id, full_name, address) VALUES (%s, %s, %s)",
            [(n, f"Persona Carga {n:04d}", f"Calle {n} # 1-1") for n in range(1, PERSONAS + 1)],
        )
        cursor.execute("SELECT document_type_id FROM document_type WHERE code = 'CC'")
        tipo_id = cursor.fetchone()[0]
        cursor.executemany(
            "INSERT INTO person_document (person_id, document_type_id, document_identifier) "
            "VALUES (%s, %s, %s)",
            [(n, tipo_id, f"50{n:08d}") for n in range(1, PERSONAS + 1)],
        )
        cursor.execute("SELECT party_role_id FROM party_role WHERE code = 'OWNER'")
        owner_id = cursor.fetchone()[0]
        cursor.executemany(
            "INSERT INTO person_party_role (person_id, party_role_id) VALUES (%s, %s)",
            [(n, owner_id) for n in range(1, PERSONAS + 1)],
        )
    conn.commit()


async def _medir(client: httpx.AsyncClient, ruta: str, params: dict[str, str]) -> float:
    inicio = time.perf_counter()
    response = await client.get(ruta, params=params)
    duracion = time.perf_counter() - inicio
    assert response.status_code == 200, response.text
    return duracion


async def test_listados_responden_en_menos_de_tres_segundos(
    client: httpx.AsyncClient, db_conn: pymysql.connections.Connection
) -> None:
    _sembrar(db_conn)

    mediciones = {
        "clientes?q=": await _medir(client, "/api/v1/clientes", {"q": "carga 04"}),
        "propietarios": await _medir(client, "/api/v1/propietarios", {}),
        "contratos?fecha_desde=": await _medir(
            client, "/api/v1/contratos", {"fecha_desde": "2026-01-01"}
        ),
    }

    lentas = {k: v for k, v in mediciones.items() if v >= LIMITE_SEGUNDOS}
    assert not lentas, f"Consultas por encima de {LIMITE_SEGUNDOS}s: {lentas}"
    total = (await client.get("/api/v1/propietarios", params={"limit": "1"})).json()["total"]
    assert total == PERSONAS
