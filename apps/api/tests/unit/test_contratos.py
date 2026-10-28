from __future__ import annotations

import httpx
import pytest

from modules.auth.schemas import Role
from tests.conftest import bearer
from tests.fakes import InMemoryBuscarRepository, InMemoryContratosRepository

pytestmark = pytest.mark.anyio

RUTA = "/api/v1/contratos"
NUEVO = {
    "tipo": "arrendamiento",
    "inmueble_id": 10,
    "fecha_inicio": "2026-01-01",
    "fecha_fin": "2026-12-31",
    "canon_pactado": "1500000.00",
    "condiciones": "Pago los primeros cinco días.",
    "texto": "CONTRATO DE ARRENDAMIENTO\n\nEntre los suscritos…",
    "arrendatario_id": 3,
    "codeudores_ids": [4, 5, 4],
}


@pytest.fixture
def datos(contratos_repository: InMemoryContratosRepository) -> InMemoryContratosRepository:
    repo = contratos_repository
    repo.persona(1, "Laura Dueña")
    repo.persona(2, "Mario Copropietario")
    repo.persona(3, "Carlos Inquilino")
    repo.persona(4, "Pedro Fiador")
    repo.persona(5, "Sofía Fiadora")
    repo.inmueble(10, "Calle 93B # 11A-44", [1, 2])
    repo.inmueble(11, "Oficina sin dueños", [])
    return repo


async def test_crear_toma_los_propietarios_del_inmueble_y_agrega_papeles(
    client: httpx.AsyncClient, datos: InMemoryContratosRepository
) -> None:
    response = await client.post(RUTA, json=NUEVO)

    assert response.status_code == 201
    body = response.json()
    assert body["tipo"] == "ARRENDAMIENTO" and body["moneda"] == "COP"
    assert [p["id"] for p in body["propietarios"]] == [1, 2]
    assert body["arrendatario"]["nombre"] == "Carlos Inquilino"
    assert [c["id"] for c in body["codeudores"]] == [4, 5]
    assert body["estado"] == "vigente" and body["dias_restantes"] == 64
    assert body["texto"].startswith("CONTRATO")
    assert datos.papeles_agregados == [
        (1, "propietario"),
        (2, "propietario"),
        (3, "arrendatario"),
        (4, "codeudor"),
        (5, "codeudor"),
    ]


async def test_crear_con_propietarios_explicitos_sin_arrendatario_ni_canon(
    client: httpx.AsyncClient, datos: InMemoryContratosRepository
) -> None:
    response = await client.post(
        RUTA,
        json={
            "tipo": "ADMINISTRACION",
            "inmueble_id": 10,
            "fecha_inicio": "2027-01-01",
            "propietarios_ids": [2],
            "arrendatario_id": None,
            "canon_pactado": None,
            "texto": "",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert [p["id"] for p in body["propietarios"]] == [2]
    assert body["arrendatario"] is None and body["codeudores"] == []
    assert body["moneda"] is None and body["texto"] is None
    assert body["estado"] == "programado" and body["dias_restantes"] is None


@pytest.mark.parametrize(
    ("cambios", "campo"),
    [
        ({"fecha_fin": "2025-12-31"}, ""),
        ({"codeudores_ids": [3]}, ""),
        ({"canon_pactado": "-1"}, "canon_pactado"),
        ({"canon_pactado": "1.234"}, "canon_pactado"),
        ({"propietarios_ids": []}, "propietarios_ids"),
        ({"texto": "con \x00 nulo"}, "texto"),
        ({"codeudores_ids": list(range(1, 12))}, "codeudores_ids"),
        ({"extra": 1}, "extra"),
        ({"fecha_inicio": "ayer"}, "fecha_inicio"),
    ],
)
async def test_validaciones_422(
    client: httpx.AsyncClient, datos: InMemoryContratosRepository, cambios: dict, campo: str
) -> None:
    response = await client.post(RUTA, json={**NUEVO, **cambios})

    assert response.status_code == 422
    detalles = response.json()["error"]["detalles"]
    assert any(d["campo"].startswith(campo) for d in detalles)
    assert "Entre los suscritos" not in response.text


async def test_tipo_inexistente_inmueble_inexistente_y_persona_inexistente(
    client: httpx.AsyncClient, datos: InMemoryContratosRepository
) -> None:
    tipo = await client.post(RUTA, json={**NUEVO, "tipo": "COMODATO"})
    inmueble = await client.post(RUTA, json={**NUEVO, "inmueble_id": 99})
    persona = await client.post(RUTA, json={**NUEVO, "arrendatario_id": 77})
    sin_duenos = await client.post(RUTA, json={**NUEVO, "inmueble_id": 11})

    assert (tipo.status_code, tipo.json()["error"]["codigo"]) == (422, "catalogo_invalido")
    assert inmueble.json()["error"]["codigo"] == "inmueble_no_encontrado"
    assert persona.json()["error"]["codigo"] == "persona_no_encontrada"
    assert (sin_duenos.status_code, sin_duenos.json()["error"]["codigo"]) == (
        409,
        "inmueble_sin_propietario",
    )


async def test_fecha_desde_invalida_422(client: httpx.AsyncClient) -> None:
    assert (await client.get(RUTA, params={"fecha_desde": "2026-13-01"})).status_code == 422
    assert (await client.get(RUTA, params={"estado": "otro"})).status_code == 422


@pytest.mark.parametrize(
    ("params", "esperado"),
    [
        ({"fecha_desde": "2026-07-01"}, ["B"]),
        ({"fecha_hasta": "2026-01-01"}, ["A"]),
        ({"fecha_desde": "2026-06-30", "fecha_hasta": "2026-09-01"}, ["B", "A"]),
        ({"fecha_desde": "2027-01-01"}, ["B"]),
        ({"estado": "finalizado"}, ["A"]),
        ({"estado": "vigente"}, ["B"]),
        ({"inquilino_id": 3}, ["A"]),
        ({"propietario_id": 1}, ["A"]),
        ({"tipo": "administracion"}, ["B"]),
        ({"q": "fiador"}, ["A"]),
        ({"q": "93b"}, ["B", "A"]),
    ],
)
async def test_filtros_y_solapamiento_de_vigencias(
    client: httpx.AsyncClient, datos: InMemoryContratosRepository, params: dict, esperado: list
) -> None:
    # A: 2026-01-01 → 2026-06-30 (finalizado el 2026-10-28); B: 2026-09-01 → indefinido.
    a = await client.post(RUTA, json={**NUEVO, "fecha_fin": "2026-06-30", "texto": "A"})
    b = await client.post(
        RUTA,
        json={
            **NUEVO,
            "tipo": "ADMINISTRACION",
            "fecha_inicio": "2026-09-01",
            "fecha_fin": None,
            "propietarios_ids": [2],
            "arrendatario_id": None,
            "codeudores_ids": [],
            "texto": "B",
        },
    )
    ids = {"A": a.json()["id"], "B": b.json()["id"]}

    response = await client.get(RUTA, params=params)

    assert response.status_code == 200
    assert [c["id"] for c in response.json()["items"]] == [ids[n] for n in esperado]
    assert "texto" not in response.json()["items"][0]  # el listado omite el texto completo


async def test_por_vencer_y_detalle_con_texto(
    client: httpx.AsyncClient, datos: InMemoryContratosRepository
) -> None:
    pronto = await client.post(RUTA, json={**NUEVO, "fecha_fin": "2026-11-30"})
    await client.post(RUTA, json={**NUEVO, "fecha_fin": "2027-06-30"})

    listado = await client.get(RUTA, params={"estado": "por_vencer"})
    detalle = await client.get(f"{RUTA}/{pronto.json()['id']}")

    assert [c["id"] for c in listado.json()["items"]] == [pronto.json()["id"]]
    assert listado.json()["items"][0]["dias_restantes"] == 33
    assert detalle.json()["texto"].startswith("CONTRATO") and detalle.json()["condiciones"]


async def test_actualizar_reemplaza_partes(
    client: httpx.AsyncClient, datos: InMemoryContratosRepository
) -> None:
    creado = await client.post(RUTA, json=NUEVO)

    response = await client.put(
        f"{RUTA}/{creado.json()['id']}",
        json={**NUEVO, "propietarios_ids": [1], "arrendatario_id": 5, "codeudores_ids": [4]},
    )

    assert response.status_code == 200
    body = response.json()
    assert [p["id"] for p in body["propietarios"]] == [1]
    assert body["arrendatario"]["id"] == 5 and [c["id"] for c in body["codeudores"]] == [4]
    assert (await client.put(f"{RUTA}/999", json=NUEVO)).status_code == 404


async def test_dependencias_bloquean_put_y_delete(
    client: httpx.AsyncClient, datos: InMemoryContratosRepository
) -> None:
    creado = await client.post(RUTA, json=NUEVO)
    agreement_id = creado.json()["id"]
    datos.dependencias[agreement_id] = (2, 1)

    editado = await client.put(f"{RUTA}/{agreement_id}", json=NUEVO)
    eliminado = await client.delete(f"{RUTA}/{agreement_id}")

    assert editado.status_code == eliminado.status_code == 409
    assert editado.json()["error"]["codigo"] == "contrato_con_dependencias"
    assert "2 registro(s) financiero(s) y 1 archivo(s)" in eliminado.json()["error"]["mensaje"]
    datos.dependencias.pop(agreement_id)
    assert (await client.delete(f"{RUTA}/{agreement_id}")).status_code == 204
    assert (await client.delete(f"{RUTA}/{agreement_id}")).status_code == 404


async def test_asesor_crea_y_edita_pero_no_elimina(
    db_client: httpx.AsyncClient, datos: InMemoryContratosRepository
) -> None:
    asesor = bearer("3", (Role.ASESOR,))

    creado = await db_client.post(RUTA, json=NUEVO, headers=asesor)
    agreement_id = creado.json()["id"]
    editado = await db_client.put(f"{RUTA}/{agreement_id}", json=NUEVO, headers=asesor)
    eliminado = await db_client.delete(f"{RUTA}/{agreement_id}", headers=asesor)

    assert (creado.status_code, editado.status_code, eliminado.status_code) == (201, 200, 403)
    assert (await db_client.get(RUTA)).status_code == 401


async def test_buscar_global(
    client: httpx.AsyncClient, buscar_repository: InMemoryBuscarRepository
) -> None:
    corto = await client.get("/api/v1/buscar", params={"q": "a"})
    vacio = await client.get("/api/v1/buscar", params={"q": "  calle 93  "})

    assert corto.status_code == 422
    assert vacio.status_code == 200
    assert vacio.json() == {"personas": [], "inmuebles": [], "contratos": []}
    assert buscar_repository.consultas == ["calle 93"]
