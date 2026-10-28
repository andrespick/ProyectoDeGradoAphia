from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime

import httpx
import pytest
from fastapi import FastAPI

from core.config import Settings
from main import create_app
from modules.clientes.router import get_clientes_repository
from modules.clientes.schemas import Cliente
from modules.clientes.service import CorreoDuplicadoError

ORIGEN_WEB = "http://localhost:5173"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


class InMemoryClientesRepository:
    """Repositorio falso para pruebas unitarias (sin MySQL)."""

    def __init__(self) -> None:
        self.items: list[Cliente] = []

    async def listar(self, *, limit: int, offset: int) -> tuple[list[Cliente], int]:
        ordered = sorted(self.items, key=lambda c: c.id, reverse=True)
        return ordered[offset : offset + limit], len(self.items)

    async def crear(self, *, nombre: str, correo: str) -> Cliente:
        if any(c.correo == correo for c in self.items):
            raise CorreoDuplicadoError()
        now = datetime.now(UTC)
        cliente = Cliente(
            id=len(self.items) + 1, nombre=nombre, correo=correo, creado_en=now, actualizado_en=now
        )
        self.items.append(cliente)
        return cliente


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
    return application


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as http:
        yield http
