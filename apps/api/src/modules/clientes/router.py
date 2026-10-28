from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from db.connection import Database
from db.dependencies import get_database
from modules.auth.dependencies import require_roles
from modules.auth.schemas import LECTURA
from modules.clientes.repository import ClientesRepository
from modules.clientes.schemas import Cliente, ClienteCreate, ClientesPage
from modules.clientes.service import ClientesRepositoryPort, ClientesService

router = APIRouter(
    prefix="/api/v1/clientes",
    tags=["clientes"],
    dependencies=[Depends(require_roles(*LECTURA))],
)


def get_clientes_repository(
    db: Annotated[Database, Depends(get_database)],
) -> ClientesRepositoryPort:
    return ClientesRepository(db)


def get_clientes_service(
    repository: Annotated[ClientesRepositoryPort, Depends(get_clientes_repository)],
) -> ClientesService:
    return ClientesService(repository)


Service = Annotated[ClientesService, Depends(get_clientes_service)]


@router.get("", response_model=ClientesPage)
async def listar_clientes(
    service: Service,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0, le=100_000)] = 0,
) -> ClientesPage:
    return await service.listar(limit=limit, offset=offset)


@router.post("", response_model=Cliente, status_code=status.HTTP_201_CREATED)
async def crear_cliente(datos: ClienteCreate, service: Service) -> Cliente:
    return await service.crear(datos)
