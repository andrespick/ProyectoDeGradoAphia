from __future__ import annotations

import time
from collections.abc import AsyncIterator, Iterable

import httpx
import pytest
from fastapi import FastAPI

from core.config import Settings
from main import create_app
from modules.auth.dependencies import get_auth_repository
from modules.auth.schemas import Role
from modules.auth.tokens import TokenPayload, issue_token
from modules.buscar.router import get_buscar_repository
from modules.catalogos.router import get_catalogos_repository
from modules.contratos.router import get_contratos_repository
from modules.inmuebles.router import get_inmuebles_repository
from modules.personas.router import get_personas_repository
from modules.resumen.router import get_resumen_repository
from modules.usuarios.router import get_usuarios_repository
from tests.fakes import (
    InMemoryAuthRepository,
    InMemoryBuscarRepository,
    InMemoryCatalogosRepository,
    InMemoryContratosRepository,
    InMemoryInmueblesRepository,
    InMemoryPersonasRepository,
    InMemoryResumenRepository,
    InMemoryUsuariosRepository,
)

ORIGEN_WEB = "http://localhost:5173"
SECRET = "secreto-de-pruebas-de-al-menos-32-caracteres"


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


def bearer(sujeto: str = "1", roles: Iterable[Role] = (Role.ADMIN_SISTEMAS,)) -> dict[str, str]:
    """Cabecera con un token válido firmado con el secreto de pruebas."""
    payload = TokenPayload(
        sub=sujeto,
        nombre=f"Usuario {sujeto}",
        roles=[role.value for role in roles],
        exp=int(time.time()) + 3600,
    )
    return {"Authorization": f"Bearer {issue_token(SECRET, payload)}"}


@pytest.fixture
def settings() -> Settings:
    return make_settings()


@pytest.fixture
def personas_repository() -> InMemoryPersonasRepository:
    return InMemoryPersonasRepository()


@pytest.fixture
def inmuebles_repository() -> InMemoryInmueblesRepository:
    return InMemoryInmueblesRepository()


@pytest.fixture
def contratos_repository() -> InMemoryContratosRepository:
    return InMemoryContratosRepository()


@pytest.fixture
def buscar_repository() -> InMemoryBuscarRepository:
    return InMemoryBuscarRepository()


@pytest.fixture
def auth_repository() -> InMemoryAuthRepository:
    return InMemoryAuthRepository()


@pytest.fixture
def usuarios_repository() -> InMemoryUsuariosRepository:
    return InMemoryUsuariosRepository()


def _with_fakes(
    application: FastAPI,
    personas_repository: InMemoryPersonasRepository,
    auth_repository: InMemoryAuthRepository,
    usuarios_repository: InMemoryUsuariosRepository,
    inmuebles_repository: InMemoryInmueblesRepository,
    contratos_repository: InMemoryContratosRepository,
    buscar_repository: InMemoryBuscarRepository,
) -> FastAPI:
    application.dependency_overrides[get_personas_repository] = lambda: personas_repository
    application.dependency_overrides[get_inmuebles_repository] = lambda: inmuebles_repository
    application.dependency_overrides[get_contratos_repository] = lambda: contratos_repository
    application.dependency_overrides[get_buscar_repository] = lambda: buscar_repository
    application.dependency_overrides[get_catalogos_repository] = InMemoryCatalogosRepository
    application.dependency_overrides[get_auth_repository] = lambda: auth_repository
    application.dependency_overrides[get_usuarios_repository] = lambda: usuarios_repository
    application.dependency_overrides[get_resumen_repository] = InMemoryResumenRepository
    return application


@pytest.fixture
def app(
    settings: Settings,
    personas_repository: InMemoryPersonasRepository,
    auth_repository: InMemoryAuthRepository,
    usuarios_repository: InMemoryUsuariosRepository,
    inmuebles_repository: InMemoryInmueblesRepository,
    contratos_repository: InMemoryContratosRepository,
    buscar_repository: InMemoryBuscarRepository,
) -> FastAPI:
    """Aplicación en modo development (usuario ficticio admin_sistemas)."""
    return _with_fakes(
        create_app(settings),
        personas_repository,
        auth_repository,
        usuarios_repository,
        inmuebles_repository,
        contratos_repository,
        buscar_repository,
    )


@pytest.fixture
def db_app(
    personas_repository: InMemoryPersonasRepository,
    auth_repository: InMemoryAuthRepository,
    usuarios_repository: InMemoryUsuariosRepository,
    inmuebles_repository: InMemoryInmueblesRepository,
    contratos_repository: InMemoryContratosRepository,
    buscar_repository: InMemoryBuscarRepository,
) -> FastAPI:
    """Aplicación en modo database: exige un token (ver ``bearer``) o iniciar sesión."""
    application = create_app(make_settings(auth_mode="database", auth_secret=SECRET))
    return _with_fakes(
        application,
        personas_repository,
        auth_repository,
        usuarios_repository,
        inmuebles_repository,
        contratos_repository,
        buscar_repository,
    )


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as http:
        yield http


@pytest.fixture
async def db_client(db_app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=db_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as http:
        yield http
