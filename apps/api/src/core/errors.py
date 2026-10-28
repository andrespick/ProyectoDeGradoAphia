"""Errores de la aplicación y su conversión centralizada a respuestas JSON.

Formato de error::

    {"error": {"codigo": "...", "mensaje": "...", "request_id": "...", "detalles": [...]}}

Las respuestas nunca incluyen trazas, sentencias SQL ni los valores enviados por el cliente.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.logging import get_logger, log_event

logger = get_logger("errors")


class AppError(Exception):
    status_code = 500
    code = "error_interno"
    default_message = "Ocurrió un error inesperado."
    headers: dict[str, str] | None = None

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = 404
    code = "no_encontrado"
    default_message = "El recurso solicitado no existe."


class ConflictError(AppError):
    status_code = 409
    code = "conflicto"
    default_message = "La operación entra en conflicto con datos existentes."


class AuthenticationRequiredError(AppError):
    status_code = 401
    code = "no_autenticado"
    default_message = "Se requiere autenticación."
    headers = {"WWW-Authenticate": "Bearer"}  # noqa: RUF012 - constante de clase


class PermissionDeniedError(AppError):
    status_code = 403
    code = "sin_permiso"
    default_message = "No tiene permisos para realizar esta operación."


class ServiceUnavailableError(AppError):
    status_code = 503
    code = "servicio_no_disponible"
    default_message = "El servicio no está disponible temporalmente."


class DatabaseUnavailableError(ServiceUnavailableError):
    code = "base_de_datos_no_disponible"
    default_message = "La base de datos no está disponible."


class DatabaseNotConfiguredError(DatabaseUnavailableError):
    code = "base_de_datos_no_configurada"
    default_message = "La conexión a la base de datos no está configurada."


_HTTP_CODES = {
    400: "solicitud_invalida",
    404: "no_encontrado",
    405: "metodo_no_permitido",
    413: "contenido_demasiado_grande",
    415: "tipo_no_soportado",
}


def request_id_of(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def error_response(
    status_code: int,
    code: str,
    message: str,
    request_id: str | None,
    details: list[dict[str, Any]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {"codigo": code, "mensaje": message, "request_id": request_id}
    if details:
        body["detalles"] = details
    return JSONResponse({"error": body}, status_code=status_code, headers=headers)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        if exc.status_code >= 500:
            log_event(
                logger,
                logging.WARNING,
                "app_error",
                code=exc.code,
                path=request.url.path,
                request_id=request_id_of(request),
            )
        return error_response(
            exc.status_code, exc.code, exc.message, request_id_of(request), headers=exc.headers
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = [_validation_detail(err) for err in exc.errors()]
        return error_response(
            422,
            "validacion",
            "Los datos enviados no son válidos.",
            request_id_of(request),
            details=details,
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = _HTTP_CODES.get(exc.status_code, "error_http")
        message = exc.detail if isinstance(exc.detail, str) else "Solicitud no procesada."
        if exc.status_code == 404:
            message = NotFoundError.default_message
        return error_response(
            exc.status_code, code, message, request_id_of(request), headers=exc.headers
        )


def _validation_detail(error: Any) -> dict[str, Any]:
    # Se omiten deliberadamente "input" y "ctx" para no reflejar los datos recibidos.
    location = [str(part) for part in error.get("loc", ())]
    origin = location[0] if location else "body"
    field = ".".join(location[1:]) if len(location) > 1 else origin
    return {
        "campo": field,
        "ubicacion": origin,
        "mensaje": error.get("msg", ""),
        "tipo": error.get("type", ""),
    }
