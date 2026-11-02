from __future__ import annotations

from fastapi import Request

from core.runtime import get_settings
from db.config import DatabaseConfig
from db.connection import Database


def get_database(request: Request) -> Database:
    """MySQL según las variables ``DB_*`` del entorno."""
    return Database(DatabaseConfig.from_settings(get_settings(request)))
