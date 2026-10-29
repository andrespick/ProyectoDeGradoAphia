from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from db.connection import Database
from db.dependencies import get_database
from modules.auth.dependencies import Auditar, require_roles
from modules.auth.schemas import GESTION_SISTEMA
from modules.contratos.router import get_contratos_service
from modules.contratos.service import ContratosService
from modules.inmuebles.router import get_inmuebles_service
from modules.inmuebles.service import InmueblesService
from modules.papelera.repository import PapeleraRepository
from modules.papelera.schemas import PapeleraPage, Restaurado, TipoRegistro
from modules.papelera.service import PapeleraRepositoryPort, PapeleraService
from modules.personas.router import get_personas_service
from modules.personas.service import PersonasService

router = APIRouter(
    prefix="/api/v1/papelera",
    tags=["papelera"],
    dependencies=[Depends(require_roles(*GESTION_SISTEMA))],
)


def get_papelera_repository(
    db: Annotated[Database, Depends(get_database)],
) -> PapeleraRepositoryPort:
    return PapeleraRepository(db)


def get_papelera_service(
    repository: Annotated[PapeleraRepositoryPort, Depends(get_papelera_repository)],
    personas: Annotated[PersonasService, Depends(get_personas_service)],
    inmuebles: Annotated[InmueblesService, Depends(get_inmuebles_service)],
    contratos: Annotated[ContratosService, Depends(get_contratos_service)],
) -> PapeleraService:
    return PapeleraService(repository, personas, inmuebles, contratos)


Service = Annotated[PapeleraService, Depends(get_papelera_service)]


@router.get("", response_model=PapeleraPage)
async def listar_papelera(
    service: Service,
    tipo: TipoRegistro | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0, le=100_000)] = 0,
) -> PapeleraPage:
    return await service.listar(tipo, limit=limit, offset=offset)


@router.post("/{id}/restaurar", response_model=Restaurado)
async def restaurar(id: int, service: Service, auditar: Auditar) -> Restaurado:
    registro, restaurado = await service.restaurar(id)
    await auditar.registrar(
        "restaurar",
        restaurado.tipo,
        restaurado.id,
        f"desde la papelera (antes #{registro.entidad_id})",
    )
    return restaurado


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_definitivamente(id: int, service: Service, auditar: Auditar) -> Response:
    await service.eliminar(id)
    await auditar.registrar("eliminar_definitivo", "papelera", id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
