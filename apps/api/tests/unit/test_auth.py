from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
import pytest
from fastapi import Depends, FastAPI

from core.config import ConfigurationError, Settings
from main import create_app
from modules.auth.dependencies import get_current_principal, require_roles
from modules.auth.schemas import Principal, Role
from tests.conftest import bearer, make_settings
from tests.fakes import InMemoryAuthRepository

pytestmark = pytest.mark.anyio

LOGIN = "/api/v1/auth/login"
ME = "/api/v1/auth/me"


def _client(app: FastAPI) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver")


def _asesor() -> Principal:
    return Principal(sujeto="u1", nombre="Asesor Ficticio", roles=[Role.ASESOR], modo="development")


async def test_modo_desarrollo_entrega_usuario_ficticio(client: httpx.AsyncClient) -> None:
    response = await client.get(ME)

    assert response.status_code == 200
    assert response.json() == {
        "sujeto": "desarrollo-local",
        "nombre": "Usuario de desarrollo",
        "roles": ["admin_sistemas", "administrativo"],
        "modo": "development",
        "debe_cambiar_clave": False,
    }


async def test_modo_desarrollo_no_permite_iniciar_sesion(client: httpx.AsyncClient) -> None:
    response = await client.post(LOGIN, json={"usuario": "admin", "clave": "x"})

    assert response.status_code == 401


@pytest.mark.parametrize("app_env", ["development", "test", "staging", "production"])
async def test_sin_autenticacion_configurada_responde_401(app_env: str) -> None:
    app = create_app(make_settings(app_env=app_env, auth_mode="disabled"))

    async with _client(app) as client:
        me = await client.get(ME)
        clientes = await client.get("/api/v1/clientes")

    assert me.status_code == 401
    assert clientes.status_code == 401
    assert clientes.headers["www-authenticate"] == "Bearer"
    assert clientes.json()["error"]["codigo"] == "no_autenticado"


async def test_modo_desarrollo_ignorado_fuera_de_local() -> None:
    # Aunque Settings se construyera saltándose la validación, la dependencia no concede acceso.
    app = create_app(make_settings(app_env="production", auth_mode="development"))

    async with _client(app) as client:
        response = await client.get(ME)

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


class TestLogin:
    async def test_login_correcto_entrega_token_y_me_lo_acepta(
        self, db_client: httpx.AsyncClient, auth_repository: InMemoryAuthRepository
    ) -> None:
        auth_repository.agregar("ana", "Clave.Segura1", roles=(Role.ADMINISTRATIVO,))

        response = await db_client.post(LOGIN, json={"usuario": " ana ", "clave": "Clave.Segura1"})

        assert response.status_code == 200
        body = response.json()
        assert body["principal"] == {
            "sujeto": "1",
            "nombre": "Persona ana",
            "roles": ["administrativo"],
            "modo": "database",
            "debe_cambiar_clave": False,
        }
        assert body["expira_en"].endswith("Z") or "+00:00" in body["expira_en"]
        assert "Clave" not in response.text

        me = await db_client.get(ME, headers={"Authorization": f"Bearer {body['token']}"})
        assert me.status_code == 200
        assert me.json() == body["principal"]

    @pytest.mark.parametrize(
        "headers",
        [
            {},
            {"Authorization": "Bearer no-es-un-token"},
            {"Authorization": "Basic abc"},
            {"Authorization": f"Bearer {bearer()['Authorization'][7:][:-3]}xyz"},
        ],
        ids=["sin-token", "malformado", "otro-esquema", "firma-alterada"],
    )
    async def test_sin_token_valido_responde_401(
        self, db_client: httpx.AsyncClient, headers: dict[str, str]
    ) -> None:
        response = await db_client.get(ME, headers=headers)

        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"

    async def test_token_con_rol_desconocido_responde_401(
        self, db_client: httpx.AsyncClient
    ) -> None:
        from modules.auth.tokens import TokenPayload, issue_token
        from tests.conftest import SECRET

        token = issue_token(
            SECRET, TokenPayload(sub="1", nombre="x", roles=["consulta"], exp=2**31)
        )

        response = await db_client.get(ME, headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 401

    async def test_clave_incorrecta_y_usuario_inexistente_responden_igual(
        self, db_client: httpx.AsyncClient, auth_repository: InMemoryAuthRepository
    ) -> None:
        auth_repository.agregar("ana", "Clave.Segura1")

        incorrecta = await db_client.post(LOGIN, json={"usuario": "ana", "clave": "otra"})
        inexistente = await db_client.post(LOGIN, json={"usuario": "nadie", "clave": "otra"})

        assert incorrecta.status_code == inexistente.status_code == 401
        assert incorrecta.json()["error"]["codigo"] == "credenciales_invalidas"
        assert incorrecta.json()["error"]["mensaje"] == inexistente.json()["error"]["mensaje"]
        assert auth_repository.por_id(1).failed_login_attempts == 1

    async def test_cuenta_inactiva_responde_401(
        self, db_client: httpx.AsyncClient, auth_repository: InMemoryAuthRepository
    ) -> None:
        auth_repository.agregar("ana", "Clave.Segura1", is_active=False)

        response = await db_client.post(LOGIN, json={"usuario": "ana", "clave": "Clave.Segura1"})

        assert response.status_code == 401
        assert response.json()["error"]["codigo"] == "credenciales_invalidas"

    async def test_tres_intentos_fallidos_bloquean_quince_minutos(
        self, db_client: httpx.AsyncClient, auth_repository: InMemoryAuthRepository
    ) -> None:
        auth_repository.agregar("ana", "Clave.Segura1")

        respuestas = [
            await db_client.post(LOGIN, json={"usuario": "ana", "clave": "mala"}) for _ in range(3)
        ]
        bloqueada = await db_client.post(LOGIN, json={"usuario": "ana", "clave": "Clave.Segura1"})

        assert [r.status_code for r in respuestas] == [401, 401, 423]
        assert respuestas[2].json()["error"]["codigo"] == "cuenta_bloqueada"
        assert "15 minuto" in respuestas[2].json()["error"]["mensaje"]
        cuenta = auth_repository.por_id(1)
        assert cuenta.failed_login_attempts == 3
        assert cuenta.locked_until is not None
        # Con la clave correcta sigue bloqueada mientras no venza el plazo.
        assert bloqueada.status_code == 423

    async def test_bloqueo_vencido_permite_entrar_y_reinicia_intentos(
        self, db_client: httpx.AsyncClient, auth_repository: InMemoryAuthRepository
    ) -> None:
        auth_repository.agregar(
            "ana",
            "Clave.Segura1",
            attempts=3,
            locked_until=datetime.now(UTC) - timedelta(seconds=1),
        )

        response = await db_client.post(LOGIN, json={"usuario": "ana", "clave": "Clave.Segura1"})

        assert response.status_code == 200
        cuenta = auth_repository.por_id(1)
        assert cuenta.failed_login_attempts == 0
        assert cuenta.locked_until is None

    async def test_bloqueo_vencido_y_clave_mala_reinicia_el_conteo_en_uno(
        self, db_client: httpx.AsyncClient, auth_repository: InMemoryAuthRepository
    ) -> None:
        auth_repository.agregar(
            "ana",
            "Clave.Segura1",
            attempts=3,
            locked_until=datetime.now(UTC) - timedelta(minutes=1),
        )

        response = await db_client.post(LOGIN, json={"usuario": "ana", "clave": "mala"})

        assert response.status_code == 401
        assert auth_repository.por_id(1).failed_login_attempts == 1

    @pytest.mark.parametrize(
        "payload",
        [
            {"usuario": "ana"},
            {"usuario": "", "clave": "x"},
            {"usuario": "ana", "clave": "x", "recordar": True},
            {"usuario": "a" * 256, "clave": "x"},
        ],
    )
    async def test_cuerpo_invalido_responde_422(
        self, db_client: httpx.AsyncClient, payload: dict[str, object]
    ) -> None:
        response = await db_client.post(LOGIN, json=payload)

        assert response.status_code == 422

    async def test_logs_de_login_no_incluyen_usuario_ni_clave(
        self,
        db_client: httpx.AsyncClient,
        auth_repository: InMemoryAuthRepository,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        auth_repository.agregar("ana.secreta", "Clave.Segura1")

        await db_client.post(LOGIN, json={"usuario": "ana.secreta", "clave": "ClaveMala99"})
        await db_client.post(LOGIN, json={"usuario": "nadie.aqui", "clave": "ClaveMala99"})

        logs = capsys.readouterr().out
        assert '"event": "login_failed"' in logs
        assert "ana.secreta" not in logs
        assert "nadie.aqui" not in logs
        assert "ClaveMala99" not in logs


@pytest.mark.parametrize(
    ("ruta", "esperado"),
    [
        ("/api/v1/usuarios", 200),
        ("/api/v1/catalogos", 200),
        ("/api/v1/resumen", 200),
        ("/api/v1/clientes", 403),
        ("/api/v1/propietarios", 403),
        ("/api/v1/inmuebles", 403),
        ("/api/v1/contratos", 403),
        ("/api/v1/buscar?q=ana", 403),
    ],
)
async def test_admin_sistemas_solo_accede_a_la_gestion_del_sistema(
    db_client: httpx.AsyncClient, ruta: str, esperado: int
) -> None:
    response = await db_client.get(ruta, headers=bearer(roles=(Role.ADMIN_SISTEMAS,)))

    assert response.status_code == esperado
