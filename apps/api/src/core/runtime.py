"""Resolución de la configuración según el runtime (Cloudflare Workers o ASGI tradicional)."""

from __future__ import annotations

from functools import lru_cache

from fastapi import Request
from starlette.types import Scope

from core.config import Settings
from integrations import cloudflare


@lru_cache(maxsize=1)
def _settings_from_environ() -> Settings:
    return Settings.from_environ()


def settings_from_scope(scope: Scope) -> Settings:
    """En Workers lee el ``env`` de la solicitud; en Uvicorn, las variables del proceso."""
    env = cloudflare.worker_env(scope)
    if env is not None:
        return Settings.from_getter(cloudflare.env_getter(env))
    return _settings_from_environ()


def clear_settings_cache() -> None:
    _settings_from_environ.cache_clear()


def runtime_name(scope: Scope) -> str:
    return "workers" if cloudflare.worker_env(scope) is not None else "asgi"


def get_settings(request: Request) -> Settings:
    """Dependencia FastAPI: configuración resuelta por ``RequestContextMiddleware``."""
    return request.state.settings
