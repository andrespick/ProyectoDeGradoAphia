from __future__ import annotations

import time
from collections.abc import AsyncIterator, Callable, Iterable
from typing import Any

import httpx
import pytest
from fastapi import FastAPI

from core.config import Settings
from main import create_app
from modules.auditoria.dependencies import get_auditoria_repository
from modules.auth.dependencies import get_auth_repository
from modules.auth.schemas import Role
from modules.auth.tokens import TokenPayload, issue_token
from modules.buscar.router import get_buscar_repository
from modules.catalogos.router import get_catalogos_admin_repository, get_catalogos_repository
from modules.configuracion.dependencies import get_configuracion_repository
from modules.contratos.router import get_contratos_repository
from modules.inmuebles.router import get_inmuebles_repository
from modules.papelera.router import get_papelera_repository
from modules.personas.router import get_personas_repository
from modules.resumen.router import get_resumen_repository
from modules.sistema.router import get_sistema_repository
from modules.usuarios.router import get_usuarios_repository
from tests.fakes import (
    InMemoryAuditoriaRepository,
    InMemoryAuthRepository,
    InMemoryBuscarRepository,
    InMemoryCatalogosAdminRepository,
    InMemoryCatalogosRepository,
    InMemoryConfiguracionRepository,
    InMemoryContratosRepository,
    InMemoryInmueblesRepository,
    InMemoryPapeleraRepository,
    InMemoryPersonasRepository,
    InMemoryResumenRepository,
    InMemorySistemaRepository,
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


def bearer(
    sujeto: str = "1", roles: Iterable[Role] = (Role.ADMIN_SISTEMAS,), ver: int = 0
) -> dict[str, str]:
    """Cabecera con un token válido firmado con el secreto de pruebas."""
    payload = TokenPayload(
        sub=sujeto,
        nombre=f"Usuario {sujeto}",
        roles=[role.value for role in roles],
        exp=int(time.time()) + 3600,
        ver=ver,
    )
    return {"Authorization": f"Bearer {issue_token(SECRET, payload)}"}


@pytest.fixture
def settings() -> Settings:
    return make_settings()


@pytest.fixture
def papelera_repository() -> InMemoryPapeleraRepository:
    return InMemoryPapeleraRepository()


@pytest.fixture
def personas_repository(
    papelera_repository: InMemoryPapeleraRepository,
) -> InMemoryPersonasRepository:
    return InMemoryPersonasRepository(papelera_repository)


@pytest.fixture
def inmuebles_repository(
    papelera_repository: InMemoryPapeleraRepository,
) -> InMemoryInmueblesRepository:
    return InMemoryInmueblesRepository(papelera_repository)


@pytest.fixture
def contratos_repository(
    papelera_repository: InMemoryPapeleraRepository,
) -> InMemoryContratosRepository:
    return InMemoryContratosRepository(papelera_repository)


@pytest.fixture
def buscar_repository() -> InMemoryBuscarRepository:
    return InMemoryBuscarRepository()


@pytest.fixture
def auth_repository() -> InMemoryAuthRepository:
    return InMemoryAuthRepository()


@pytest.fixture
def usuarios_repository() -> InMemoryUsuariosRepository:
    return InMemoryUsuariosRepository()


@pytest.fixture
def auditoria_repository() -> InMemoryAuditoriaRepository:
    return InMemoryAuditoriaRepository()


@pytest.fixture
def configuracion_repository() -> InMemoryConfiguracionRepository:
    return InMemoryConfiguracionRepository()


@pytest.fixture
def sistema_repository() -> InMemorySistemaRepository:
    return InMemorySistemaRepository()


@pytest.fixture
def catalogos_admin_repository() -> InMemoryCatalogosAdminRepository:
    return InMemoryCatalogosAdminRepository()


@pytest.fixture
def overrides(
    personas_repository: InMemoryPersonasRepository,
    auth_repository: InMemoryAuthRepository,
    usuarios_repository: InMemoryUsuariosRepository,
    inmuebles_repository: InMemoryInmueblesRepository,
    contratos_repository: InMemoryContratosRepository,
    buscar_repository: InMemoryBuscarRepository,
    papelera_repository: InMemoryPapeleraRepository,
    auditoria_repository: InMemoryAuditoriaRepository,
    configuracion_repository: InMemoryConfiguracionRepository,
    sistema_repository: InMemorySistemaRepository,
    catalogos_admin_repository: InMemoryCatalogosAdminRepository,
) -> dict[Callable[..., Any], Callable[[], Any]]:
    """Cada ``get_*_repository`` de la app se sustituye por su repositorio en memoria."""
    return {
        get_personas_repository: lambda: personas_repository,
        get_inmuebles_repository: lambda: inmuebles_repository,
        get_contratos_repository: lambda: contratos_repository,
        get_buscar_repository: lambda: buscar_repository,
        get_catalogos_repository: InMemoryCatalogosRepository,
        get_catalogos_admin_repository: lambda: catalogos_admin_repository,
        get_auth_repository: lambda: auth_repository,
        get_usuarios_repository: lambda: usuarios_repository,
        get_resumen_repository: InMemoryResumenRepository,
        get_papelera_repository: lambda: papelera_repository,
        get_auditoria_repository: lambda: auditoria_repository,
        get_configuracion_repository: lambda: configuracion_repository,
        get_sistema_repository: lambda: sistema_repository,
    }


@pytest.fixture
def app(settings: Settings, overrides: dict[Callable[..., Any], Callable[[], Any]]) -> FastAPI:
    """Aplicación en modo development (usuario ficticio admin_sistemas + administrativo)."""
    application = create_app(settings)
    application.dependency_overrides.update(overrides)
    return application


@pytest.fixture
def db_app(overrides: dict[Callable[..., Any], Callable[[], Any]]) -> FastAPI:
    """Aplicación en modo database: exige un token (ver ``bearer``) o iniciar sesión."""
    application = create_app(make_settings(auth_mode="database", auth_secret=SECRET))
    application.dependency_overrides.update(overrides)
    return application


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
