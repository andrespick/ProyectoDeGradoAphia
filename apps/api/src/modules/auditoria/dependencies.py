from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from db.connection import Database
from db.dependencies import get_database
from modules.auditoria.repository import AuditoriaRepository
from modules.auditoria.service import AuditoriaRepositoryPort


def get_auditoria_repository(
    db: Annotated[Database, Depends(get_database)],
) -> AuditoriaRepositoryPort:
    return AuditoriaRepository(db)
