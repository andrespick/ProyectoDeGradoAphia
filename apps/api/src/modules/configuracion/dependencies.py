from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from db.connection import Database
from db.dependencies import get_database
from modules.configuracion.repository import ConfiguracionRepository
from modules.configuracion.service import ConfiguracionRepositoryPort


def get_configuracion_repository(
    db: Annotated[Database, Depends(get_database)],
) -> ConfiguracionRepositoryPort:
    return ConfiguracionRepository(db)
