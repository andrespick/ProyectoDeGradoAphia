from __future__ import annotations

import httpx
import pytest
from fastapi import Depends, FastAPI

from main import create_app
from modules.auth.dependencies import get_current_principal, require_roles
from modules.auth.schemas import Principal, Role
from tests.conftest import make_settings

pytestmark = pytest.mark.anyio


def _client(app: FastAPI) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver")


async def test_modo_desarrollo_entrega_usuario_ficticio(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 200
    assert response.json() == {
        "sujeto": "desarrollo-local",
        "nombre": "Usuario de desarrollo",
        "roles": ["admin"],
        "modo": "development",
    }


@pytest.mark.parametrize("app_env", ["development", "test", "staging", "production"])
async def test_sin_autenticacion_configurada_responde_401(app_env: str) -> None:
    app = create_app(make_settings(app_env=app_env, auth_mode="disabled"))

    async with _client(app) as client:
        me = await client.get("/api/v1/auth/me")
        clientes = await client.get("/api/v1/clientes")

    assert me.status_code == 401
    assert clientes.status_code == 401
    assert clientes.headers["www-authenticate"] == "Bearer"
    assert clientes.json()["error"]["codigo"] == "no_autenticado"


async def test_modo_desarrollo_ignorado_fuera_de_local() -> None:
    # Aunque Settings se construyera saltándose la validación, la dependencia no concede acceso.
    app = create_app(make_settings(app_env="production", auth_mode="development"))

    async with _client(app) as client:
        response = await client.get("/api/v1/auth/me")

    assert response.status_code == 401


async def test_rol_insuficiente_responde_403() -> None:
    app = create_app(make_settings())

    @app.get("/api/prueba-roles")
    async def solo_consulta(
        principal: Principal = Depends(require_roles(Role.CONSULTA)),  # noqa: B008
    ) -> dict[str, str]:
        return {"sujeto": principal.sujeto}

    async with _client(app) as client:
        response = await client.get("/api/prueba-roles")

    assert response.status_code == 403
    assert response.json()["error"]["codigo"] == "sin_permiso"


async def test_rol_permitido() -> None:
    app = create_app(make_settings())
    app.dependency_overrides[get_current_principal] = lambda: Principal(
        sujeto="u1", nombre="Asesor Ficticio", roles=[Role.ASESOR], modo="development"
    )

    @app.get("/api/prueba-roles")
    async def solo_asesor(
        principal: Principal = Depends(require_roles(Role.ASESOR)),  # noqa: B008
    ) -> dict[str, str]:
        return {"sujeto": principal.sujeto}

    async with _client(app) as client:
        response = await client.get("/api/prueba-roles")

    assert response.status_code == 200
