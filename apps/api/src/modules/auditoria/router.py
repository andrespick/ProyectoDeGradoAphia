from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from modules.auditoria.dependencies import get_auditoria_repository
from modules.auditoria.schemas import AuditoriaFiltros, AuditoriaPage
from modules.auditoria.service import AuditoriaRepositoryPort
from modules.auth.dependencies import require_roles
from modules.auth.schemas import GESTION_SISTEMA

router = APIRouter(
    prefix="/api/v1/auditoria",
    tags=["auditoria"],
    dependencies=[Depends(require_roles(*GESTION_SISTEMA))],
)


@router.get("", response_model=AuditoriaPage)
async def listar_eventos(
    repository: Annotated[AuditoriaRepositoryPort, Depends(get_auditoria_repository)],
    accion: Annotated[str | None, Query(max_length=50)] = None,
    entidad: Annotated[str | None, Query(max_length=50)] = None,
    entidad_id: Annotated[int | None, Query(ge=1)] = None,
    q: Annotated[str | None, Query(max_length=100)] = None,
    desde: date | None = None,
    hasta: date | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0, le=100_000)] = 0,
) -> AuditoriaPage:
    filtros = AuditoriaFiltros(
        accion=accion, entidad=entidad, entidad_id=entidad_id, q=q, desde=desde, hasta=hasta
    )
    items, total = await repository.listar(filtros, limit=limit, offset=offset)
    return AuditoriaPage(items=items, total=total, limit=limit, offset=offset)
