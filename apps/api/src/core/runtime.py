"""Configuración del proceso (variables de entorno y Docker secrets).

Se lee una vez y ``RequestContextMiddleware`` la deja en cada solicitud; las pruebas pueden
fijar otra con ``create_app(settings)``.
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import Request

from core.config import Settings


@lru_cache(maxsize=1)
def settings_from_environ() -> Settings:
    return Settings.from_environ()


def get_settings(request: Request) -> Settings:
    """Dependencia FastAPI: configuración resuelta por ``RequestContextMiddleware``."""
    return request.state.settings
