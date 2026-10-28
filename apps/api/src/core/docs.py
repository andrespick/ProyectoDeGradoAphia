"""Documentación OpenAPI disponible solo en entornos locales (development/test)."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse

from core.errors import NotFoundError
from core.runtime import get_settings

_DOCS_CSP = (
    "default-src 'none'; script-src https://cdn.jsdelivr.net 'unsafe-inline'; "
    "style-src https://cdn.jsdelivr.net 'unsafe-inline'; img-src data: https:; "
    "connect-src 'self'; frame-ancestors 'none'"
)


def add_local_docs(app: FastAPI) -> None:
    @app.get("/api/openapi.json", include_in_schema=False)
    async def openapi_schema(request: Request) -> JSONResponse:
        _ensure_local(request)
        return JSONResponse(app.openapi())

    @app.get("/api/docs", include_in_schema=False)
    async def swagger_ui(request: Request) -> HTMLResponse:
        _ensure_local(request)
        response = get_swagger_ui_html(openapi_url="/api/openapi.json", title="APHIA API")
        response.headers["content-security-policy"] = _DOCS_CSP
        return response


def _ensure_local(request: Request) -> None:
    if not get_settings(request).is_local:
        raise NotFoundError()
