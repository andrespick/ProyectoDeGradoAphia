from __future__ import annotations

from fastapi import Request

from core.runtime import get_settings
from db.config import DatabaseConfig
from db.connection import Database
from integrations import cloudflare


def get_database(request: Request) -> Database:
    """Workers: binding Hyperdrive. Uvicorn: variables ``DB_*``."""
    env = cloudflare.worker_env(request.scope)
    config = cloudflare.hyperdrive_config(env) if env is not None else None
    if config is None:
        config = DatabaseConfig.from_settings(get_settings(request))
    return Database(config)
