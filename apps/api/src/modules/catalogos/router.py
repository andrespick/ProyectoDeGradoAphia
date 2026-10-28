from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from db.connection import Database
from db.dependencies import get_database
from modules.auth.dependencies import require_roles
from modules.auth.schemas import LECTURA
from modules.catalogos.repository import CatalogosRepository, CatalogosRepositoryPort
from modules.catalogos.schemas import Catalogos

router = APIRouter(
    prefix="/api/v1/catalogos",
    tags=["catalogos"],
    dependencies=[Depends(require_roles(*LECTURA))],
)


def get_catalogos_repository(
    db: Annotated[Database, Depends(get_database)],
) -> CatalogosRepositoryPort:
    return CatalogosRepository(db)


@router.get("", response_model=Catalogos)
async def obtener_catalogos(
    repository: Annotated[CatalogosRepositoryPort, Depends(get_catalogos_repository)],
) -> Catalogos:
    return await repository.obtener()
