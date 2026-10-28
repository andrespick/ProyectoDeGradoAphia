"""Simula el runtime de Cloudflare Workers: el ``env`` llega en ``scope["env"]``."""

from __future__ import annotations

from types import SimpleNamespace

import httpx
import pytest
from starlette.types import ASGIApp, Receive, Scope, Send

from db.config import DatabaseConfig
from integrations import cloudflare
from main import create_app

pytestmark = pytest.mark.anyio


def fake_env(**vars_: object) -> SimpleNamespace:
    hyperdrive = SimpleNamespace(
        host="hyperdrive.local", port="5555", user="u", password="p", database="aphia"
    )
    defaults = {"APP_ENV": "staging", "CORS_ORIGINS": "https://staging.example.pages.dev"}
    return SimpleNamespace(**{**defaults, **vars_}, HYPERDRIVE=hyperdrive)


def with_env(app: ASGIApp, env: object) -> ASGIApp:
    async def wrapper(scope: Scope, receive: Receive, send: Send) -> None:
        await app({**scope, "env": env}, receive, send)

    return wrapper


def test_hyperdrive_config_desde_binding() -> None:
    config = cloudflare.hyperdrive_config(fake_env())

    assert config == DatabaseConfig(
        host="hyperdrive.local", port=5555, user="u", password="p", database="aphia"
    )


def test_sin_binding_hyperdrive() -> None:
    assert cloudflare.hyperdrive_config(SimpleNamespace()) is None


def test_env_getter() -> None:
    get = cloudflare.env_getter(SimpleNamespace(APP_ENV="production"))

    assert get("APP_ENV") == "production"
    assert get("NO_EXISTE") is None


async def test_configuracion_se_lee_del_env_de_workers() -> None:
    app = with_env(create_app(), fake_env())

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="https://api.example"
    ) as client:
        health = await client.get(
            "/api/health", headers={"Origin": "https://staging.example.pages.dev"}
        )
        clientes = await client.get("/api/v1/clientes")

    assert health.json()["runtime"] == "workers"
    assert health.json()["environment"] == "staging"
    assert health.headers["access-control-allow-origin"] == "https://staging.example.pages.dev"
    assert "strict-transport-security" in health.headers
    assert clientes.status_code == 401  # staging sin autenticación real
