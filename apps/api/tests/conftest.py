from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi import FastAPI

from core.config import Settings
from main import create_app
from modules.catalogos.router import get_catalogos_repository
from modules.clientes.router import get_clientes_repository
from tests.fakes import InMemoryCatalogosRepository, InMemoryClientesRepository

ORIGEN_WEB = "http://localhost:5173"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def make_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "app_env": "test",
        "cors_origins": (ORIGEN_WEB,),
        "auth_mode": "development",
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


@pytest.fixture
def settings() -> Settings:
    return make_settings()


@pytest.fixture
def repository() -> InMemoryClientesRepository:
    return InMemoryClientesRepository()


@pytest.fixture
def app(settings: Settings, repository: InMemoryClientesRepository) -> FastAPI:
    application = create_app(settings)
    application.dependency_overrides[get_clientes_repository] = lambda: repository
    application.dependency_overrides[get_catalogos_repository] = InMemoryCatalogosRepository
    return application


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as http:
        yield http
