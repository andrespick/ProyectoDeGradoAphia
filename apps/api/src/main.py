"""Aplicación FastAPI de APHIA (ASGI estándar).

- Linux/Uvicorn:      ``uvicorn main:app --app-dir src``
- Cloudflare Workers: ``entry.py`` envuelve esta misma ``app``.

Este módulo no importa nada específico de Cloudflare.
"""

from __future__ import annotations

import os

from fastapi import FastAPI

from core.config import Settings
from core.docs import add_local_docs
from core.errors import register_exception_handlers
from core.logging import configure_logging
from core.middleware import RequestContextMiddleware, SettingsCORSMiddleware
from core.runtime import settings_from_scope
from modules.auth.router import router as auth_router
from modules.catalogos.router import router as catalogos_router
from modules.clientes.router import router as clientes_router
from modules.codeudores.router import router as codeudores_router
from modules.health.router import API_VERSION
from modules.health.router import router as health_router
from modules.inmuebles.router import router as inmuebles_router
from modules.personas.router import router as personas_router
from modules.propietarios.router import router as propietarios_router
from modules.resumen.router import router as resumen_router
from modules.usuarios.router import router as usuarios_router


def create_app(settings: Settings | None = None) -> FastAPI:
    """``settings`` fija la configuración (pruebas); si es ``None`` se resuelve por solicitud."""
    configure_logging(settings.log_level if settings else os.environ.get("LOG_LEVEL", "INFO"))

    app = FastAPI(
        title="APHIA API",
        version=API_VERSION,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(personas_router)
    app.include_router(clientes_router)
    app.include_router(propietarios_router)
    app.include_router(codeudores_router)
    app.include_router(inmuebles_router)
    app.include_router(catalogos_router)
    app.include_router(usuarios_router)
    app.include_router(resumen_router)
    add_local_docs(app)

    provider = (lambda _scope: settings) if settings is not None else settings_from_scope
    # El último middleware agregado es el más externo.
    app.add_middleware(SettingsCORSMiddleware)
    app.add_middleware(RequestContextMiddleware, settings_provider=provider)
    return app


app = create_app()
