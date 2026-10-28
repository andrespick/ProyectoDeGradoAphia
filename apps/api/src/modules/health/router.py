"""Endpoints de disponibilidad.

- ``/api/health``: el proceso responde (no toca dependencias externas).
- ``/api/ready``: la API puede atender solicitudes reales (MySQL accesible).
"""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.errors import ServiceUnavailableError
from core.runtime import get_settings, runtime_name
from db.connection import Database
from db.dependencies import get_database

router = APIRouter(prefix="/api", tags=["sistema"])

API_VERSION = "0.1.0"


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str
    environment: str
    runtime: Literal["workers", "asgi"]


class ReadyResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    checks: dict[str, Literal["ok", "unavailable"]]


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="aphia-api",
        version=API_VERSION,
        environment=get_settings(request).app_env,
        runtime=runtime_name(request.scope),
    )


@router.get("/ready", response_model=ReadyResponse, responses={503: {"model": ReadyResponse}})
async def ready(db: Annotated[Database, Depends(get_database)]) -> ReadyResponse | JSONResponse:
    try:
        await db.ping()
    except ServiceUnavailableError:
        body = ReadyResponse(status="not_ready", checks={"database": "unavailable"})
        return JSONResponse(body.model_dump(), status_code=503)
    return ReadyResponse(status="ready", checks={"database": "ok"})
