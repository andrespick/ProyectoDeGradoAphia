from __future__ import annotations

import httpx
import pytest

from modules.auth.schemas import Role
from tests.conftest import bearer
from tests.fakes import InMemoryUsuariosRepository

pytestmark = pytest.mark.anyio

RUTA = "/api/v1/usuarios"
NUEVO = {
    "usuario": "mperez",
    "nombre": "  María   Pérez ",
    "tipo_identificacion": "cc",
    "identificacion": "1020304050",
    "correo": "Maria.Perez@Example.test",
    "clave": "Clave.Segura1",
    "rol": "asesor",
}


def _update(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "nombre": "María Pérez",
        "tipo_identificacion": "CC",
        "identificacion": "1020304050",
        "correo": "maria.perez@example.test",
        "rol": "asesor",
        "activo": True,
    }
    base.update(overrides)
    return base


async def test_crear_y_listar(
    client: httpx.AsyncClient, usuarios_repository: InMemoryUsuariosRepository
) -> None:
    created = await client.post(RUTA, json=NUEVO)

    assert created.status_code == 201
    body = created.json()
    assert body["usuario"] == "mperez"
    assert body["nombre"] == "María Pérez"
    assert body["tipo_identificacion"] == "CC"
    assert body["correo"] == "maria.perez@example.test"
    assert body["rol"] == "asesor"
    assert body["activo"] is True and body["bloqueada"] is False
    assert "clave" not in body and "Clave.Segura1" not in created.text
    assert usuarios_repository.hashes[body["id"]].startswith("pbkdf2_sha256$")

    listed = await client.get(RUTA, params={"q": "pérez"})
    assert listed.json()["total"] == 1
    assert (await client.get(RUTA, params={"rol": "administrativo"})).json()["total"] == 0
    assert (await client.get(RUTA, params={"estado": "activo"})).json()["total"] == 1


@pytest.mark.parametrize(
    ("cambios", "campo"),
    [
        ({"usuario": "MPerez"}, "usuario"),
        ({"usuario": "m perez"}, "usuario"),
        ({"usuario": "mp"}, "usuario"),
        ({"clave": "12345678"}, "clave"),
        ({"clave": "Corta1"}, "clave"),
        ({"rol": "consulta"}, "rol"),
        ({"correo": "no-es-correo"}, "correo"),
        ({"identificacion": "12 34"}, "identificacion"),
        ({"nombre": "Con\x00control"}, "nombre"),
        ({"extra": 1}, "extra"),
    ],
)
async def test_validacion_de_entradas(
    client: httpx.AsyncClient, cambios: dict[str, object], campo: str
) -> None:
    response = await client.post(RUTA, json={**NUEVO, **cambios})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["codigo"] == "validacion"
    assert campo in {d["campo"] for d in error["detalles"]}
    assert "Clave.Segura1" not in response.text


async def test_usuario_duplicado_responde_409(client: httpx.AsyncClient) -> None:
    assert (await client.post(RUTA, json=NUEVO)).status_code == 201

    response = await client.post(RUTA, json={**NUEVO, "identificacion": "999"})

    assert response.status_code == 409
    assert response.json()["error"]["codigo"] == "usuario_duplicado"


async def test_obtener_inexistente_responde_404(client: httpx.AsyncClient) -> None:
    response = await client.get(f"{RUTA}/99")

    assert response.status_code == 404
    assert response.json()["error"]["codigo"] == "usuario_no_encontrado"


async def test_actualizar_sin_clave_conserva_el_hash(
    client: httpx.AsyncClient, usuarios_repository: InMemoryUsuariosRepository
) -> None:
    created = (await client.post(RUTA, json=NUEVO)).json()
    hash_previo = usuarios_repository.hashes[created["id"]]

    response = await client.put(
        f"{RUTA}/{created['id']}", json=_update(nombre="María P. Gómez", rol="administrativo")
    )

    assert response.status_code == 200
    assert response.json()["nombre"] == "María P. Gómez"
    assert response.json()["rol"] == "administrativo"
    assert usuarios_repository.hashes[created["id"]] == hash_previo

    con_clave = await client.put(f"{RUTA}/{created['id']}", json=_update(clave="Otra.Clave2"))
    assert con_clave.status_code == 200
    assert usuarios_repository.hashes[created["id"]] != hash_previo


async def test_ultimo_administrador_no_se_degrada_ni_desactiva_ni_elimina(
    client: httpx.AsyncClient, usuarios_repository: InMemoryUsuariosRepository
) -> None:
    admin = usuarios_repository.agregar("root", Role.ADMIN_SISTEMAS)

    degradar = await client.put(f"{RUTA}/{admin.id}", json=_update(rol="asesor"))
    desactivar = await client.put(
        f"{RUTA}/{admin.id}", json=_update(rol="admin_sistemas", activo=False)
    )
    eliminar = await client.delete(f"{RUTA}/{admin.id}")

    for response in (degradar, desactivar, eliminar):
        assert response.status_code == 409
        assert response.json()["error"]["codigo"] == "ultimo_administrador"

    usuarios_repository.agregar("root2", Role.ADMIN_SISTEMAS)
    assert (await client.put(f"{RUTA}/{admin.id}", json=_update(rol="asesor"))).status_code == 200


async def test_no_se_puede_eliminar_ni_desactivar_la_cuenta_propia(
    db_client: httpx.AsyncClient, usuarios_repository: InMemoryUsuariosRepository
) -> None:
    yo = usuarios_repository.agregar("yo", Role.ADMIN_SISTEMAS)
    usuarios_repository.agregar("otro", Role.ADMIN_SISTEMAS)
    headers = bearer(sujeto=str(yo.id))

    eliminar = await db_client.delete(f"{RUTA}/{yo.id}", headers=headers)
    desactivar = await db_client.put(
        f"{RUTA}/{yo.id}", json=_update(rol="admin_sistemas", activo=False), headers=headers
    )

    assert eliminar.status_code == desactivar.status_code == 409
    assert eliminar.json()["error"]["codigo"] == "usuario_actual"


async def test_eliminar_responde_204_y_luego_404(
    client: httpx.AsyncClient, usuarios_repository: InMemoryUsuariosRepository
) -> None:
    usuario = usuarios_repository.agregar("asesor1", Role.ASESOR)

    assert (await client.delete(f"{RUTA}/{usuario.id}")).status_code == 204
    assert (await client.delete(f"{RUTA}/{usuario.id}")).status_code == 404


async def test_desbloquear(
    client: httpx.AsyncClient,
    usuarios_repository: InMemoryUsuariosRepository,
    capsys: pytest.CaptureFixture[str],
) -> None:
    usuario = usuarios_repository.agregar("bloqueada", Role.ASESOR, bloqueada=True)
    assert (await client.get(RUTA, params={"estado": "bloqueado"})).json()["total"] == 1

    response = await client.post(f"{RUTA}/{usuario.id}/desbloquear")

    assert response.status_code == 200
    assert response.json()["bloqueada"] is False
    assert response.json()["intentos_fallidos"] == 0
    assert '"event": "usuario_desbloqueado"' in capsys.readouterr().out


@pytest.mark.parametrize("rol", [Role.ADMINISTRATIVO, Role.ASESOR])
async def test_otros_roles_reciben_403_en_todos_los_endpoints(
    db_client: httpx.AsyncClient, rol: Role
) -> None:
    headers = bearer(sujeto="9", roles=(rol,))

    respuestas = [
        await db_client.get(RUTA, headers=headers),
        await db_client.get(f"{RUTA}/1", headers=headers),
        await db_client.post(RUTA, json=NUEVO, headers=headers),
        await db_client.put(f"{RUTA}/1", json=_update(), headers=headers),
        await db_client.delete(f"{RUTA}/1", headers=headers),
        await db_client.post(f"{RUTA}/1/desbloquear", headers=headers),
    ]

    assert [r.status_code for r in respuestas] == [403] * 6


async def test_sin_token_responde_401(db_client: httpx.AsyncClient) -> None:
    response = await db_client.get(RUTA)

    assert response.status_code == 401
