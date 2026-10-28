from __future__ import annotations

from datetime import date

import httpx
import pytest

from modules.auth.schemas import Role
from modules.personas.schemas import ContratoResumen, Dependencias, InmuebleResumen
from tests.conftest import bearer
from tests.fakes import InMemoryPersonasRepository

pytestmark = pytest.mark.anyio

CLIENTE = {
    "nombre": "  Ana   María  García ",
    "tipo_identificacion": "cc",
    "identificacion": "1020304050",
    "telefono": "+57 300 123 4567",
    "correo": "Ana.Garcia@Example.test",
    "papeles": ["arrendatario"],
}
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


async def test_crear_cliente_con_papel_y_listar(client: httpx.AsyncClient) -> None:
    created = await client.post("/api/v1/clientes", json=CLIENTE)

    assert created.status_code == 201
    body = created.json()
    assert body["nombre"] == "Ana María García"
    assert body["tipo_identificacion"] == "CC"
    assert body["correo"] == "ana.garcia@example.test"
    assert body["papeles"] == ["arrendatario"]
    assert body["cuenta_bancaria"] is None

    listed = await client.get("/api/v1/clientes")
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["identificacion"] == "1020304050"


async def test_identificacion_duplicada_responde_409(client: httpx.AsyncClient) -> None:
    assert (await client.post("/api/v1/clientes", json=CLIENTE)).status_code == 201

    response = await client.post(
        "/api/v1/propietarios", json={**PROPIETARIO, "identificacion": "1020304050"}
    )

    assert response.status_code == 409
    assert response.json()["error"]["codigo"] == "identificacion_duplicada"


@pytest.mark.parametrize(
    ("cambios", "campo"),
    [
        ({"identificacion": "12 34"}, "identificacion"),
        ({"identificacion": "12"}, "identificacion"),
        ({"correo": "no-es-correo"}, "correo"),
        ({"telefono": "abc"}, "telefono"),
        ({"papeles": []}, "papeles"),
        ({"papeles": ["inquilino"]}, "papeles"),
        ({"nombre": "Con\x00control"}, "nombre"),
        ({"extra": 1}, "extra"),
        (
            {"cuenta_bancaria": {"banco": "B", "tipo": "AHORROS", "numero": "AB-1"}},
            "cuenta_bancaria.numero",
        ),
    ],
)
async def test_validacion_de_entradas(
    client: httpx.AsyncClient, cambios: dict[str, object], campo: str
) -> None:
    response = await client.post("/api/v1/clientes", json={**CLIENTE, **cambios})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["codigo"] == "validacion"
    assert any(d["campo"].startswith(campo) for d in error["detalles"])
    assert "1020304050" not in response.text


async def test_campos_opcionales_vacios_se_guardan_como_nulos(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/clientes", json={**CLIENTE, "telefono": "", "correo": "  ", "direccion": ""}
    )

    assert response.status_code == 201
    assert response.json()["telefono"] is None
    assert response.json()["correo"] is None


async def test_post_propietarios_y_codeudores_agregan_su_papel(client: httpx.AsyncClient) -> None:
    propietario = await client.post(
        "/api/v1/propietarios", json={**PROPIETARIO, "papeles": ["arrendatario"]}
    )
    codeudor = await client.post(
        "/api/v1/codeudores", json={**CLIENTE, "identificacion": "777", "papeles": ["codeudor"]}
    )

    assert propietario.status_code == 201
    assert propietario.json()["papeles"] == ["propietario", "arrendatario"]
    assert propietario.json()["cuenta_bancaria"]["tipo"] == "AHORROS"
    assert codeudor.json()["papeles"] == ["codeudor"]


async def test_cada_lista_muestra_solo_su_papel(
    client: httpx.AsyncClient, personas_repository: InMemoryPersonasRepository
) -> None:
    personas_repository.agregar("Dueña", "1001", ["propietario"])
    personas_repository.agregar("Inquilino", "1002", ["arrendatario"])
    personas_repository.agregar("Ambos", "1003", ["propietario", "codeudor"])
    personas_repository.agregar("Solo cuenta de usuario", "1004", [])

    clientes = await client.get("/api/v1/clientes")
    propietarios = await client.get("/api/v1/propietarios")
    codeudores = await client.get("/api/v1/codeudores")
    por_papel = await client.get("/api/v1/clientes?papel=arrendatario")

    assert [p["nombre"] for p in clientes.json()["items"]] == ["Ambos", "Inquilino", "Dueña"]
    assert [p["nombre"] for p in propietarios.json()["items"]] == ["Ambos", "Dueña"]
    assert [p["nombre"] for p in codeudores.json()["items"]] == ["Ambos"]
    assert [p["nombre"] for p in por_papel.json()["items"]] == ["Inquilino"]


async def test_filtros_por_nombre_identificacion_correo_y_contrato(
    client: httpx.AsyncClient, personas_repository: InMemoryPersonasRepository
) -> None:
    ana = personas_repository.agregar("Ana García", "1020", ["codeudor"], correo="ana@example.test")
    personas_repository.agregar("Luis Pérez", "3040", ["propietario"], correo="luis@example.test")
    personas_repository.codeudores_por_contrato[7] = {ana.id}

    assert (await client.get("/api/v1/clientes?q=garc")).json()["total"] == 1
    assert (await client.get("/api/v1/clientes?q=3040")).json()["total"] == 1
    assert (await client.get("/api/v1/propietarios?correo=luis")).json()["total"] == 1
    assert (await client.get("/api/v1/codeudores?contrato_id=7")).json()["total"] == 1
    assert (await client.get("/api/v1/codeudores?contrato_id=8")).json()["total"] == 0


async def test_detalle_incluye_relaciones(
    client: httpx.AsyncClient, personas_repository: InMemoryPersonasRepository
) -> None:
    persona = personas_repository.agregar("Mario", "1009", ["propietario", "codeudor"])
    inmueble = InmuebleResumen(id=5, direccion="Calle 5", ciudad="Bogotá", estado="OCUPADO")
    contrato = ContratoResumen(
        id=3, tipo="ARRENDAMIENTO", fecha_inicio=date(2026, 1, 1), fecha_fin=None, inmueble=inmueble
    )
    personas_repository.inmuebles[persona.id] = [inmueble]
    personas_repository.contratos[persona.id] = {"codeudor": [contrato]}
    personas_repository.usuarios[persona.id] = "mario"

    response = await client.get(f"/api/v1/clientes/{persona.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["inmuebles"][0]["direccion"] == "Calle 5"
    assert body["contratos_como_codeudor"][0]["inmueble"]["ciudad"] == "Bogotá"
    assert body["contratos_como_arrendatario"] == []
    assert body["usuario"] == "mario"
    assert (await client.get("/api/v1/clientes/99")).status_code == 404


async def test_actualizar_contacto_papeles_y_cuenta(
    client: httpx.AsyncClient, personas_repository: InMemoryPersonasRepository
) -> None:
    persona = personas_repository.agregar("Ana", "1020", ["arrendatario"])

    response = await client.put(
        f"/api/v1/clientes/{persona.id}",
        json={**PROPIETARIO, "identificacion": "1020", "papeles": ["arrendatario", "propietario"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["papeles"] == ["propietario", "arrendatario"]
    assert body["cuenta_bancaria"]["banco"] == "Bancolombia"
    assert body["direccion"] == "Calle 1 # 2-3"


async def test_quitar_papel_en_uso_responde_409(
    client: httpx.AsyncClient, personas_repository: InMemoryPersonasRepository
) -> None:
    persona = personas_repository.agregar("Dueña", "1001", ["propietario", "arrendatario"])
    personas_repository.dependencias[persona.id] = Dependencias(
        inmuebles=2, por_papel={"propietario": 2, "arrendatario": 0, "codeudor": 0}
    )

    quitar_propietario = await client.put(
        f"/api/v1/clientes/{persona.id}", json={**CLIENTE, "identificacion": "1001"}
    )
    quitar_arrendatario = await client.put(
        f"/api/v1/clientes/{persona.id}",
        json={**CLIENTE, "identificacion": "1001", "papeles": ["propietario"]},
    )

    assert quitar_propietario.status_code == 409
    assert quitar_propietario.json()["error"]["codigo"] == "papel_en_uso"
    assert quitar_arrendatario.status_code == 200
    # El router de propietarios nunca deja quitar su propio papel.
    assert (
        await client.put(
            f"/api/v1/propietarios/{persona.id}", json={**CLIENTE, "identificacion": "1001"}
        )
    ).status_code == 200
    assert "propietario" in (await client.get(f"/api/v1/clientes/{persona.id}")).json()["papeles"]


async def test_eliminar_con_dependencias_responde_409_con_el_motivo(
    client: httpx.AsyncClient, personas_repository: InMemoryPersonasRepository
) -> None:
    persona = personas_repository.agregar("Dueña", "1001", ["propietario"])
    personas_repository.dependencias[persona.id] = Dependencias(
        inmuebles=2, contratos=1, usuarios=1
    )

    response = await client.delete(f"/api/v1/propietarios/{persona.id}")

    assert response.status_code == 409
    error = response.json()["error"]
    assert error["codigo"] == "persona_con_dependencias"
    assert "propietaria de 2 inmueble(s)" in error["mensaje"]
    assert "participa en 1 contrato(s)" in error["mensaje"]
    assert "cuenta de usuario" in error["mensaje"]
    assert persona.id in personas_repository.items


async def test_eliminar_ok_y_luego_404(
    client: httpx.AsyncClient, personas_repository: InMemoryPersonasRepository
) -> None:
    persona = personas_repository.agregar("Libre", "1001", ["codeudor"])

    assert (await client.delete(f"/api/v1/codeudores/{persona.id}")).status_code == 204
    assert (await client.delete(f"/api/v1/codeudores/{persona.id}")).status_code == 404


async def test_asesor_crea_y_edita_pero_no_elimina(
    db_client: httpx.AsyncClient, personas_repository: InMemoryPersonasRepository
) -> None:
    asesor = bearer("3", (Role.ASESOR,))
    persona = personas_repository.agregar("Libre", "1001", ["codeudor"])

    crear = await db_client.post("/api/v1/clientes", json=CLIENTE, headers=asesor)
    editar = await db_client.put(
        f"/api/v1/clientes/{persona.id}", json={**CLIENTE, "identificacion": "1001"}, headers=asesor
    )
    eliminar = await db_client.delete(f"/api/v1/clientes/{persona.id}", headers=asesor)
    administrativo = await db_client.delete(
        f"/api/v1/clientes/{persona.id}", headers=bearer("2", (Role.ADMINISTRATIVO,))
    )

    assert crear.status_code == 201
    assert editar.status_code == 200
    assert eliminar.status_code == 403
    assert administrativo.status_code == 204


async def test_buscar_por_identificacion(
    client: httpx.AsyncClient, personas_repository: InMemoryPersonasRepository
) -> None:
    personas_repository.agregar("Sin papel", "1020", [])

    encontrada = await client.get(
        "/api/v1/personas/buscar", params={"tipo_identificacion": "cc", "identificacion": "1020"}
    )
    ausente = await client.get(
        "/api/v1/personas/buscar", params={"tipo_identificacion": "CC", "identificacion": "9"}
    )
    incompleta = await client.get("/api/v1/personas/buscar", params={"identificacion": "1020"})

    assert encontrada.status_code == 200
    assert encontrada.json()["nombre"] == "Sin papel"
    assert ausente.status_code == 404
    assert incompleta.status_code == 422


@pytest.mark.parametrize(
    "query", ["limit=0", "limit=101", "offset=-1", "limit=abc", "contrato_id=0"]
)
async def test_paginacion_invalida_responde_422(client: httpx.AsyncClient, query: str) -> None:
    response = await client.get(f"/api/v1/clientes?{query}")

    assert response.status_code == 422


async def test_paginacion(
    client: httpx.AsyncClient, personas_repository: InMemoryPersonasRepository
) -> None:
    for i in range(3):
        personas_repository.agregar(f"Persona {i}", str(100 + i), ["arrendatario"])

    response = await client.get("/api/v1/clientes?limit=2&offset=1")

    page = response.json()
    assert page["total"] == 3
    assert [p["nombre"] for p in page["items"]] == ["Persona 1", "Persona 0"]


async def test_cuerpo_que_no_es_json_responde_422(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/clientes", content=b"nombre=x", headers={"content-type": "text/plain"}
    )

    assert response.status_code == 422
