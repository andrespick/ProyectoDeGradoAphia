from __future__ import annotations

import httpx
import pytest

from modules.auth.schemas import Role
from tests.conftest import bearer
from tests.fakes import (
    InMemoryAuditoriaRepository,
    InMemoryContratosRepository,
    InMemoryInmueblesRepository,
    InMemoryPapeleraRepository,
)

pytestmark = pytest.mark.anyio

PROPIETARIO = {
    "nombre": "Pedro Propietario",
    "tipo_identificacion": "CC",
    "identificacion": "55667788",
    "telefono": "3001112233",
    "correo": "pedro@example.test",
    "direccion": "Calle 1 # 2-3",
    "papeles": ["propietario"],
    "cuenta_bancaria": {"banco": "Bancolombia", "tipo": "ahorros", "numero": "0123456789"},
}


async def test_eliminar_persona_la_guarda_y_restaurar_la_crea_de_nuevo(
    client: httpx.AsyncClient,
    papelera_repository: InMemoryPapeleraRepository,
    auditoria_repository: InMemoryAuditoriaRepository,
) -> None:
    person_id = (await client.post("/api/v1/propietarios", json=PROPIETARIO)).json()["id"]

    assert (await client.delete(f"/api/v1/propietarios/{person_id}")).status_code == 204
    lista = (await client.get("/api/v1/papelera")).json()
    registro = lista["items"][0]
    restaurado = await client.post(f"/api/v1/papelera/{registro['id']}/restaurar")

    assert lista["total"] == 1
    assert registro["tipo"] == "persona"
    assert registro["entidad_id"] == person_id
    assert registro["descripcion"] == "Pedro Propietario (CC 55667788)"
    assert registro["eliminado_por"] == "Usuario de desarrollo"
    assert restaurado.status_code == 200
    nuevo = (await client.get(f"/api/v1/propietarios/{restaurado.json()['id']}")).json()
    assert nuevo["identificacion"] == "55667788"
    assert nuevo["cuenta_bancaria"]["numero"] == "0123456789"
    assert nuevo["papeles"] == ["propietario"]
    assert papelera_repository.items == {}
    assert ("restaurar", "persona", restaurado.json()["id"]) in auditoria_repository.acciones()


async def test_no_restaura_si_la_identificacion_ya_se_registro_de_nuevo(
    client: httpx.AsyncClient,
) -> None:
    person_id = (await client.post("/api/v1/propietarios", json=PROPIETARIO)).json()["id"]
    await client.delete(f"/api/v1/propietarios/{person_id}")
    await client.post("/api/v1/propietarios", json=PROPIETARIO)

    response = await client.post("/api/v1/papelera/1/restaurar")

    assert response.status_code == 409
    error = response.json()["error"]
    assert error["codigo"] == "restauracion_imposible"
    assert "identificación" in error["mensaje"]
    # Sigue en la papelera para intentarlo después.
    assert (await client.get("/api/v1/papelera")).json()["total"] == 1


async def test_inmueble_ida_y_vuelta(
    client: httpx.AsyncClient, inmuebles_repository: InMemoryInmueblesRepository
) -> None:
    inmuebles_repository.persona(1, "Laura Dueña")
    creado = await client.post(
        "/api/v1/inmuebles",
        json={
            "direccion": "Calle 93B # 11A-44",
            "ciudad": "Bogotá",
            "canon": "1500000.50",
            "estado": "disponible",
            "servicios": [{"tipo": "energia", "proveedor": "Enel", "numero_contrato": "E-1"}],
            "propietarios_ids": [1],
        },
    )
    await client.delete(f"/api/v1/inmuebles/{creado.json()['id']}")

    registro = (await client.get("/api/v1/papelera", params={"tipo": "inmueble"})).json()["items"][
        0
    ]
    restaurado = await client.post(f"/api/v1/papelera/{registro['id']}/restaurar")

    assert registro["descripcion"] == "Calle 93B # 11A-44, Bogotá"
    inmueble = (await client.get(f"/api/v1/inmuebles/{restaurado.json()['id']}")).json()
    assert inmueble["canon"] == "1500000.50"
    assert inmueble["servicios"][0]["numero_contrato"] == "E-1"
    assert [p["id"] for p in inmueble["propietarios"]] == [1]


async def test_contrato_no_se_restaura_si_su_inmueble_ya_no_existe(
    client: httpx.AsyncClient, contratos_repository: InMemoryContratosRepository
) -> None:
    contratos_repository.persona(1, "Laura Dueña")
    contratos_repository.persona(3, "Carlos Inquilino")
    contratos_repository.inmueble(10, "Calle 93B # 11A-44", [1])
    creado = await client.post(
        "/api/v1/contratos",
        json={
            "tipo": "ARRENDAMIENTO",
            "inmueble_id": 10,
            "fecha_inicio": "2026-01-01",
            "texto": "CONTRATO",
            "arrendatario_id": 3,
        },
    )
    await client.delete(f"/api/v1/contratos/{creado.json()['id']}")
    registro = (await client.get("/api/v1/papelera")).json()["items"][0]
    datos = contratos_repository.papelera.items[registro["id"]][1]

    del contratos_repository.inmuebles[10]
    response = await client.post(f"/api/v1/papelera/{registro['id']}/restaurar")

    assert registro["descripcion"] == "Contrato 1 · Calle 93B # 11A-44"
    assert datos["propietarios_ids"] == [1] and datos["arrendatario_id"] == 3
    assert response.status_code == 409
    assert "inmueble" in response.json()["error"]["mensaje"]


async def test_eliminar_definitivamente_y_404(client: httpx.AsyncClient) -> None:
    person_id = (await client.post("/api/v1/propietarios", json=PROPIETARIO)).json()["id"]
    await client.delete(f"/api/v1/propietarios/{person_id}")

    assert (await client.delete("/api/v1/papelera/1")).status_code == 204
    assert (await client.delete("/api/v1/papelera/1")).status_code == 404
    assert (await client.post("/api/v1/papelera/1/restaurar")).status_code == 404


async def test_solo_el_administrador(db_client: httpx.AsyncClient) -> None:
    administrativo = bearer(roles=(Role.ADMINISTRATIVO,))

    response = await db_client.get("/api/v1/papelera", headers=administrativo)

    assert response.status_code == 403
