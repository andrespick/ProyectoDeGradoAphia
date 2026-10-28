from __future__ import annotations

import httpx
import pytest
from fastapi import Depends, FastAPI

from core.config import ConfigurationError, Settings
from main import create_app
from modules.auth.dependencies import get_current_principal, require_roles
from modules.auth.schemas import Principal, Role
from tests.conftest import make_settings

pytestmark = pytest.mark.anyio


def _client(app: FastAPI) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver")


def _asesor() -> Principal:
    return Principal(sujeto="u1", nombre="Asesor Ficticio", roles=[Role.ASESOR], modo="development")


async def test_modo_desarrollo_entrega_usuario_ficticio(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 200
    assert response.json() == {
        "sujeto": "desarrollo-local",
        "nombre": "Usuario de desarrollo",
        "roles": ["admin_sistemas"],
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
    app.dependency_overrides[get_current_principal] = _asesor

    @app.get("/api/prueba-roles")
    async def solo_administrativo(
        principal: Principal = Depends(require_roles(Role.ADMINISTRATIVO)),  # noqa: B008
    ) -> dict[str, str]:
        return {"sujeto": principal.sujeto}

    async with _client(app) as client:
        response = await client.get("/api/prueba-roles")

    assert response.status_code == 403
    assert response.json()["error"]["codigo"] == "sin_permiso"


async def test_rol_permitido() -> None:
    app = create_app(make_settings())
    app.dependency_overrides[get_current_principal] = _asesor

    @app.get("/api/prueba-roles")
    async def solo_asesor(
        principal: Principal = Depends(require_roles(Role.ASESOR)),  # noqa: B008
    ) -> dict[str, str]:
        return {"sujeto": principal.sujeto}

    async with _client(app) as client:
        response = await client.get("/api/prueba-roles")

    assert response.status_code == 200


def test_roles_se_traducen_a_codigos_de_app_role() -> None:
    assert Role.ADMIN_SISTEMAS.code == "ADMIN_SISTEMAS"
    assert Role.from_code("ASESOR") is Role.ASESOR
    with pytest.raises(ValueError, match="consulta"):
        Role.from_code("CONSULTA")


class TestModoDatabase:
    @pytest.mark.parametrize("secreto", [None, "", "corto", "x" * 31])
    def test_exige_auth_secret_de_32_caracteres(self, secreto: str | None) -> None:
        valores = {"AUTH_MODE": "database"}
        if secreto is not None:
            valores["AUTH_SECRET"] = secreto

        with pytest.raises(ConfigurationError, match="AUTH_SECRET"):
            Settings.from_getter(valores.get)

    def test_acepta_secreto_valido_y_no_lo_muestra(self) -> None:
        settings = Settings.from_getter({"AUTH_MODE": "database", "AUTH_SECRET": "s" * 32}.get)

        assert settings.auth_mode == "database"
        assert "ssss" not in repr(settings)
