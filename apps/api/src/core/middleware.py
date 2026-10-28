"""Middleware ASGI puros (sin BaseHTTPMiddleware) compatibles con Workers y Uvicorn."""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable

from starlette.datastructures import MutableHeaders
from starlette.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from core.config import ConfigurationError, Settings
from core.errors import error_response
from core.logging import get_logger, log_event

logger = get_logger("http")

SettingsProvider = Callable[[Scope], Settings]

SECURITY_HEADERS = {
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "no-referrer",
    "content-security-policy": "default-src 'none'; frame-ancestors 'none'",
    "permissions-policy": "camera=(), microphone=(), geolocation=()",
    "cache-control": "no-store",
}
HSTS_VALUE = "max-age=31536000; includeSubDomains"


class RequestContextMiddleware:
    """Middleware externo de la API.

    - Resuelve la configuración del entorno y la deja en ``request.state.settings``.
    - Asigna un ``request_id`` y lo devuelve en ``X-Request-ID``.
    - Agrega cabeceras de seguridad a todas las respuestas.
    - Captura excepciones no controladas y responde un 500 genérico sin detalles internos.
    - Registra una línea por solicitud (método, ruta, estado, duración). No registra la
      query string ni el cuerpo porque pueden contener datos personales.
    """

    def __init__(self, app: ASGIApp, settings_provider: SettingsProvider) -> None:
        self.app = app
        self.settings_provider = settings_provider

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = uuid.uuid4().hex
        state = scope.setdefault("state", {})
        state["request_id"] = request_id
        started_at = time.perf_counter()
        response_status = {"code": 500, "started": False}
        hsts = {"enabled": False}

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                response_status["code"] = message["status"]
                response_status["started"] = True
                headers = MutableHeaders(scope=message)
                for name, value in SECURITY_HEADERS.items():
                    if name not in headers:
                        headers[name] = value
                if hsts["enabled"]:
                    headers["strict-transport-security"] = HSTS_VALUE
                headers["x-request-id"] = request_id
            await send(message)

        try:
            settings = self.settings_provider(scope)
        except ConfigurationError as exc:
            log_event(
                logger, logging.ERROR, "configuration_error", detail=str(exc), request_id=request_id
            )
            response = error_response(
                500,
                "configuracion_invalida",
                "La configuración del servicio es inválida.",
                request_id,
            )
            await response(scope, receive, send_with_headers)
            return

        state["settings"] = settings
        hsts["enabled"] = not settings.is_local

        try:
            await self.app(scope, receive, send_with_headers)
        except Exception as exc:  # último nivel de defensa
            log_event(
                logger,
                logging.ERROR,
                "unhandled_exception",
                error_type=type(exc).__name__,
                path=scope.get("path"),
                request_id=request_id,
            )
            if settings.is_local:
                logger.exception("Detalle (solo entornos locales)")
            if not response_status["started"]:
                response = error_response(
                    500, "error_interno", "Ocurrió un error inesperado.", request_id
                )
                await response(scope, receive, send_with_headers)
        finally:
            log_event(
                logger,
                logging.INFO,
                "request",
                method=scope.get("method"),
                path=scope.get("path"),
                status=response_status["code"],
                duration_ms=round((time.perf_counter() - started_at) * 1000, 1),
                request_id=request_id,
            )


class SettingsCORSMiddleware:
    """CORS con orígenes explícitos tomados de la configuración del entorno.

    En Workers la configuración solo está disponible dentro de la solicitud, por eso el
    ``CORSMiddleware`` de Starlette se crea de forma diferida y se reutiliza por cada
    lista de orígenes.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self._instances: dict[tuple[str, ...], CORSMiddleware] = {}

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        settings: Settings = scope["state"]["settings"]
        cors = self._instances.get(settings.cors_origins)
        if cors is None:
            cors = CORSMiddleware(
                self.app,
                allow_origins=list(settings.cors_origins),
                allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
                allow_headers=["Authorization", "Content-Type"],
                expose_headers=["X-Request-ID"],
                allow_credentials=False,
                max_age=600,
            )
            self._instances[settings.cors_origins] = cors
        await cors(scope, receive, send)
