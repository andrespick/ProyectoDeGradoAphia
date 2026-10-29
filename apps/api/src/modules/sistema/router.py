from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from core.runtime import get_settings, runtime_name
from db.connection import Database
from db.dependencies import get_database
from modules.auth.dependencies import Auditar, require_roles
from modules.auth.schemas import GESTION_SISTEMA
from modules.health.router import API_VERSION
from modules.sistema.repository import SistemaRepository
from modules.sistema.schemas import EstadoApi, EstadoSistema, Respaldo, RespaldosPage
from modules.sistema.service import SistemaRepositoryPort, SistemaService

router = APIRouter(
    prefix="/api/v1/sistema",
    tags=["sistema"],
    dependencies=[Depends(require_roles(*GESTION_SISTEMA))],
)


def get_sistema_repository(
    db: Annotated[Database, Depends(get_database)],
) -> SistemaRepositoryPort:
    return SistemaRepository(db)


def get_sistema_service(
    repository: Annotated[SistemaRepositoryPort, Depends(get_sistema_repository)],
) -> SistemaService:
    return SistemaService(repository)


Service = Annotated[SistemaService, Depends(get_sistema_service)]


@router.get("/estado", response_model=EstadoSistema)
async def estado(request: Request, service: Service) -> EstadoSistema:
    api = EstadoApi(
        version=API_VERSION,
        entorno=get_settings(request).app_env,
        runtime=runtime_name(request.scope),
    )
    return await service.estado(api)


@router.get("/respaldos", response_model=RespaldosPage)
async def listar_respaldos(
    service: Service,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0, le=100_000)] = 0,
) -> RespaldosPage:
    return await service.respaldos(limit=limit, offset=offset)


@router.post("/respaldos", response_model=Respaldo, status_code=status.HTTP_202_ACCEPTED)
async def solicitar_respaldo(service: Service, auditar: Auditar) -> Respaldo:
    respaldo = await service.solicitar_respaldo()
    await auditar.registrar("solicitar_respaldo", "respaldo", respaldo.id)
    return respaldo
