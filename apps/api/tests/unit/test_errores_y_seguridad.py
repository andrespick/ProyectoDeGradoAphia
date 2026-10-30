from __future__ import annotations

from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI

from core.config import ConfigurationError, Settings, read_environ
from core.errors import DatabaseUnavailableError
from main import create_app
from modules.personas.router import get_personas_repository
from tests.conftest import ORIGEN_WEB, make_settings

pytestmark = pytest.mark.anyio


def _client(app: FastAPI) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver")


async def test_ruta_inexistente_responde_404_json(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/no-existe")

    assert response.status_code == 404
    error = response.json()["error"]
    assert error["codigo"] == "no_encontrado"
    assert error["request_id"] == response.headers["x-request-id"]


async def test_metodo_no_permitido_responde_405(client: httpx.AsyncClient) -> None:
    response = await client.delete("/api/health")

    assert response.status_code == 405
    assert response.json()["error"]["codigo"] == "metodo_no_permitido"


async def test_excepcion_no_controlada_responde_500_generico(
    app: FastAPI, capsys: pytest.CaptureFixture[str]
) -> None:
    class Explota:
        async def listar(self, *_: object, **__: object) -> None:
            raise RuntimeError("detalle interno con secreto=abc123")

    app.dependency_overrides[get_personas_repository] = lambda: Explota()

    async with _client(app) as client:
        response = await client.get("/api/v1/clientes")

    assert response.status_code == 500
    error = response.json()["error"]
    assert error["codigo"] == "error_interno"
    assert "secreto" not in response.text
    assert "Traceback" not in response.text
    assert response.headers["x-content-type-options"] == "nosniff"
    logs = capsys.readouterr().out
    assert '"event": "unhandled_exception"' in logs
    assert '"error_type": "RuntimeError"' in logs


async def test_base_de_datos_caida_responde_503(app: FastAPI) -> None:
    class SinBaseDeDatos:
        async def listar(self, *_: object, **__: object) -> None:
            raise DatabaseUnavailableError()

    app.dependency_overrides[get_personas_repository] = lambda: SinBaseDeDatos()

    async with _client(app) as client:
        response = await client.get("/api/v1/clientes")

    assert response.status_code == 503
    assert response.json()["error"]["codigo"] == "base_de_datos_no_disponible"


async def test_cabeceras_de_seguridad(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/health")

    headers = response.headers
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    assert headers["referrer-policy"] == "no-referrer"
    assert headers["content-security-policy"].startswith("default-src 'none'")
    assert headers["cache-control"] == "no-store"
    assert len(headers["x-request-id"]) == 32
    assert "strict-transport-security" not in headers  # solo fuera de entornos locales


async def test_hsts_en_produccion() -> None:
    app = create_app(make_settings(app_env="production", auth_mode="disabled"))

    async with _client(app) as client:
        response = await client.get("/api/health")

    assert response.headers["strict-transport-security"].startswith("max-age=")


async def test_logs_no_incluyen_query_string(
    client: httpx.AsyncClient, capsys: pytest.CaptureFixture[str]
) -> None:
    await client.get("/api/v1/clientes?offset=0&correo=persona@example.test")

    logs = capsys.readouterr().out
    assert '"event": "request"' in logs
    assert "persona@example.test" not in logs


class TestCors:
    async def test_preflight_desde_origen_permitido(self, client: httpx.AsyncClient) -> None:
        response = await client.options(
            "/api/v1/clientes",
            headers={
                "Origin": ORIGEN_WEB,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )

        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == ORIGEN_WEB

    async def test_origen_no_permitido_no_recibe_cabeceras_cors(
        self, client: httpx.AsyncClient
    ) -> None:
        response = await client.get("/api/health", headers={"Origin": "https://malicioso.example"})

        assert "access-control-allow-origin" not in response.headers

    async def test_preflight_desde_origen_no_permitido_es_rechazado(
        self, client: httpx.AsyncClient
    ) -> None:
        response = await client.options(
            "/api/v1/clientes",
            headers={
                "Origin": "https://malicioso.example",
                "Access-Control-Request-Method": "POST",
            },
        )

        assert response.status_code == 400

    @pytest.mark.parametrize("value", ["*", "localhost:5173", "http://ok.example,*"])
    def test_comodin_u_origen_invalido_es_rechazado(self, value: str) -> None:
        with pytest.raises(ConfigurationError):
            Settings.from_getter({"CORS_ORIGINS": value}.get)


class TestConfiguracion:
    def test_valores_por_defecto(self) -> None:
        settings = Settings.from_getter({}.get)

        assert settings.app_env == "development"
        assert settings.auth_mode == "disabled"
        assert settings.cors_origins == ()

    def test_password_no_aparece_en_repr(self) -> None:
        settings = Settings.from_getter({"DB_PASSWORD": "super-secreta"}.get)

        assert "super-secreta" not in repr(settings)

    @pytest.mark.parametrize("env", ["staging", "production"])
    def test_auth_de_desarrollo_prohibida_fuera_de_local(self, env: str) -> None:
        with pytest.raises(ConfigurationError):
            Settings.from_getter({"APP_ENV": env, "AUTH_MODE": "development"}.get)

    def test_app_env_invalido(self) -> None:
        with pytest.raises(ConfigurationError):
            Settings.from_getter({"APP_ENV": "prod"}.get)

    def test_puerto_invalido(self) -> None:
        with pytest.raises(ConfigurationError):
            Settings.from_getter({"DB_PORT": "tres"}.get)

    def test_tls_hacia_mysql(self) -> None:
        assert Settings.from_getter({}.get).db_ssl_required is False
        assert Settings.from_getter({"DB_SSL_MODE": "required"}.get).db_ssl_required is True
        with pytest.raises(ConfigurationError):
            Settings.from_getter({"DB_SSL_MODE": "preferred"}.get)

    def test_secretos_por_archivo_docker(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        archivo = tmp_path / "db_password"
        archivo.write_text("desde-archivo\n", encoding="utf-8")
        monkeypatch.setenv("DB_PASSWORD_FILE", str(archivo))
        monkeypatch.setenv("DB_PASSWORD", "desde-variable")
        monkeypatch.setenv("DB_HOST", "mysql")
        assert read_environ("DB_PASSWORD") == "desde-archivo"
        assert read_environ("DB_HOST") == "mysql"
        assert read_environ("DB_INEXISTENTE") is None

    async def test_configuracion_invalida_responde_500_sin_detalles(self) -> None:
        def broken_provider(_scope: object) -> Settings:
            raise ConfigurationError("APP_ENV inválido")

        from core.middleware import RequestContextMiddleware

        app = create_app(make_settings())
        wrapped = RequestContextMiddleware(app, settings_provider=broken_provider)

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=wrapped), base_url="http://testserver"
        ) as client:
            response = await client.get("/api/health")

        assert response.status_code == 500
        assert response.json()["error"]["codigo"] == "configuracion_invalida"


async def test_docs_solo_en_entornos_locales() -> None:
    local = create_app(make_settings())
    production = create_app(make_settings(app_env="production", auth_mode="disabled"))

    async with _client(local) as client:
        assert (await client.get("/api/openapi.json")).status_code == 200
        assert (await client.get("/api/docs")).status_code == 200
    async with _client(production) as client:
        assert (await client.get("/api/openapi.json")).status_code == 404
        assert (await client.get("/api/docs")).status_code == 404
