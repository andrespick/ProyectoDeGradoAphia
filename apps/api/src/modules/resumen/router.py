from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from db.connection import Database
from db.dependencies import get_database
from modules.auth.dependencies import require_roles
from modules.auth.schemas import TODOS
from modules.resumen.repository import ResumenRepository, ResumenRepositoryPort
from modules.resumen.schemas import Resumen

router = APIRouter(
    prefix="/api/v1/resumen",
    tags=["resumen"],
    dependencies=[Depends(require_roles(*TODOS))],
)


def get_resumen_repository(
    db: Annotated[Database, Depends(get_database)],
) -> ResumenRepositoryPort:
    return ResumenRepository(db)


@router.get("", response_model=Resumen)
async def obtener_resumen(
    repository: Annotated[ResumenRepositoryPort, Depends(get_resumen_repository)],
) -> Resumen:
    return await repository.obtener()
