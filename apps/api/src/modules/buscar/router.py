from __future__ import annotations

from typing import Annotated, Protocol

from fastapi import APIRouter, Depends, Query

from db.connection import Database
from db.dependencies import get_database
from modules.auth.dependencies import require_roles
from modules.auth.schemas import LECTURA
from modules.buscar.repository import BuscarRepository
from modules.buscar.schemas import ResultadosBusqueda

router = APIRouter(
    prefix="/api/v1/buscar",
    tags=["buscar"],
    dependencies=[Depends(require_roles(*LECTURA))],
)


class BuscarRepositoryPort(Protocol):
    async def buscar(self, q: str) -> ResultadosBusqueda: ...


def get_buscar_repository(db: Annotated[Database, Depends(get_database)]) -> BuscarRepositoryPort:
    return BuscarRepository(db)


@router.get("", response_model=ResultadosBusqueda)
async def buscar(
    q: Annotated[str, Query(min_length=2, max_length=100)],
    repository: Annotated[BuscarRepositoryPort, Depends(get_buscar_repository)],
) -> ResultadosBusqueda:
    return await repository.buscar(q.strip())
