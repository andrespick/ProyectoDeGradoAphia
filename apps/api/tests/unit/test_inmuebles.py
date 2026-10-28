from __future__ import annotations

import httpx
import pytest

from modules.auth.schemas import Role
from tests.conftest import bearer
from tests.fakes import InMemoryInmueblesRepository

pytestmark = pytest.mark.anyio

RUTA = "/api/v1/inmuebles"
NUEVO = {
    "direccion": "Calle 93B # 11A-44, Apto 502",
    "ciudad": "Bogotá",
    "matricula": "50C-184920",
    "canon": "1500000.50",
    "estado": "disponible",
    "servicios": [
        {"tipo": "energia", "proveedor": "Enel", "numero_contrato": "ENEL-1"},
        {"numero_contrato": "SIN-TIPO"},
    ],
    "propietarios_ids": [1, 2, 1],
}


@pytest.fixture
def con_personas(inmuebles_repository: InMemoryInmueblesRepository) -> InMemoryInmueblesRepository:
    inmuebles_repository.persona(1, "Laura Dueña")
    inmuebles_repository.persona(2, "Mario Copropietario")
    return inmuebles_repository


async def test_crear_con_dos_propietarios_y_servicios(
    client: httpx.AsyncClient, con_personas: InMemoryInmueblesRepository
) -> None:
    response = await client.post(RUTA, json=NUEVO)

    assert response.status_code == 201
    body = response.json()
    assert body["canon"] == "1500000.50"
    assert body["moneda"] == "COP"
    assert body["estado"] == "DISPONIBLE"
    assert [p["nombre"] for p in body["propietarios"]] == ["Laura Dueña", "Mario Copropietario"]
    assert [s["tipo"] for s in body["servicios"]] == ["ENERGIA", None]
    assert con_personas.papeles_agregados == [(1, "propietario"), (2, "propietario")]


async def test_sin_canon_no_tiene_moneda(
    client: httpx.AsyncClient, con_personas: InMemoryInmueblesRepository
) -> None:
    response = await client.post(RUTA, json={**NUEVO, "canon": None, "estado": "", "servicios": []})

    assert response.status_code == 201
    assert response.json()["canon"] is None
    assert response.json()["moneda"] is None
    assert response.json()["estado"] is None


@pytest.mark.parametrize(
    ("cambios", "campo"),
    [
        ({"canon": "-1"}, "canon"),
        ({"canon": "1.234"}, "canon"),
        ({"propietarios_ids": []}, "propietarios_ids"),
        ({"servicios": [{"tipo": "AGUA"}]}, "servicios"),
        ({"direccion": "ab"}, "direccion"),
        ({"extra": 1}, "extra"),
    ],
)
async def test_validacion_de_entradas(
    client: httpx.AsyncClient,
    con_personas: InMemoryInmueblesRepository,
    cambios: dict[str, object],
    campo: str,
) -> None:
    response = await client.post(RUTA, json={**NUEVO, **cambios})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["codigo"] == "validacion"
    assert any(d["campo"].startswith(campo) for d in error["detalles"])


async def test_estado_inexistente_responde_422_y_propietario_inexistente_404(
    client: httpx.AsyncClient, con_personas: InMemoryInmueblesRepository
) -> None:
    estado = await client.post(RUTA, json={**NUEVO, "estado": "LIBRE"})
    persona = await client.post(RUTA, json={**NUEVO, "propietarios_ids": [99]})

    assert estado.status_code == 422
    assert estado.json()["error"]["codigo"] == "catalogo_invalido"
    assert persona.status_code == 404
    assert persona.json()["error"]["codigo"] == "persona_no_encontrada"


async def test_filtros(
    client: httpx.AsyncClient, con_personas: InMemoryInmueblesRepository
) -> None:
    await client.post(RUTA, json=NUEVO)
    await client.post(
        RUTA,
        json={
            **NUEVO,
            "direccion": "Carrera 7 # 1-2",
            "matricula": "M-2",
            "ciudad": "Medellín",
            "estado": "OCUPADO",
            "propietarios_ids": [2],
        },
    )

    assert (await client.get(RUTA)).json()["total"] == 2
    assert (await client.get(RUTA, params={"estado": "ocupado"})).json()["total"] == 1
    assert (await client.get(RUTA, params={"ciudad": "bog"})).json()["total"] == 1
    assert (await client.get(RUTA, params={"propietario_id": 1})).json()["total"] == 1
    assert (await client.get(RUTA, params={"q": "50C"})).json()["total"] == 1
    assert (await client.get(RUTA, params={"q": "carrera"})).json()["total"] == 1


async def test_actualizar_reemplaza_servicios_y_propietarios(
    client: httpx.AsyncClient, con_personas: InMemoryInmueblesRepository
) -> None:
    property_id = (await client.post(RUTA, json=NUEVO)).json()["id"]

    response = await client.put(
        f"{RUTA}/{property_id}",
        json={
            **NUEVO,
            "propietarios_ids": [2],
            "servicios": [{"numero_contrato": "NUEVO-1"}],
            "canon": "99.00",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert [p["id"] for p in body["propietarios"]] == [2]
    assert [s["numero_contrato"] for s in body["servicios"]] == ["NUEVO-1"]
    assert body["canon"] == "99.00"
    assert (await client.put(f"{RUTA}/99", json=NUEVO)).status_code == 404


async def test_eliminar(
    client: httpx.AsyncClient, con_personas: InMemoryInmueblesRepository
) -> None:
    property_id = (await client.post(RUTA, json=NUEVO)).json()["id"]
    con_personas.contratos[property_id] = 2

    bloqueado = await client.delete(f"{RUTA}/{property_id}")
    assert bloqueado.status_code == 409
    assert bloqueado.json()["error"]["codigo"] == "inmueble_con_contratos"
    assert "tiene 2 contrato(s)" in bloqueado.json()["error"]["mensaje"]

    con_personas.contratos[property_id] = 0
    assert (await client.delete(f"{RUTA}/{property_id}")).status_code == 204
    assert (await client.delete(f"{RUTA}/{property_id}")).status_code == 404
    assert (await client.get(f"{RUTA}/{property_id}")).status_code == 404


async def test_asesor_crea_y_edita_pero_no_elimina(
    db_client: httpx.AsyncClient, con_personas: InMemoryInmueblesRepository
) -> None:
    asesor = bearer("3", (Role.ASESOR,))

    creado = await db_client.post(RUTA, json=NUEVO, headers=asesor)
    property_id = creado.json()["id"]
    editado = await db_client.put(f"{RUTA}/{property_id}", json=NUEVO, headers=asesor)
    eliminado = await db_client.delete(f"{RUTA}/{property_id}", headers=asesor)

    assert (creado.status_code, editado.status_code, eliminado.status_code) == (201, 200, 403)
    assert (await db_client.get(RUTA)).status_code == 401
