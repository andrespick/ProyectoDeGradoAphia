"""Servicio privado de documentos de APHIA.

No está pensado para usuarios finales: solo la API lo invoca, con un token de servicio,
a través de Cloudflare Tunnel/Workers VPC en producción. No publica rutas del sistema
de archivos ni documentación OpenAPI.

Ejecución: ``uvicorn main:create_app --factory --app-dir src --port 4000``

Endpoints (todos requieren ``Authorization: Bearer <FILES_SERVICE_TOKEN>`` salvo /health):
    POST   /v1/files                 cuerpo binario; cabeceras Content-Type y X-Filename
    GET    /v1/files/{id}            descarga
    GET    /v1/files/{id}/metadata   metadatos
    DELETE /v1/files/{id}            eliminación
"""

from __future__ import annotations

import hmac
import json
import logging
import sys
from typing import Annotated, Any
from urllib.parse import quote, unquote

from fastapi import APIRouter, Depends, FastAPI, Header, Request, Response
from fastapi.responses import FileResponse, JSONResponse

from config import FilesSettings
from storage import (
    EmptyFileError,
    FileTooLargeError,
    InvalidFileIdError,
    LocalFileStorage,
    StoredFileNotFoundError,
    UnsupportedFileTypeError,
)

logger = logging.getLogger("aphia.files")


def _log(level: int, event: str, **fields: Any) -> None:
    logger.log(level, json.dumps({"event": event, **fields}, ensure_ascii=False))


class ServiceError(Exception):
    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


_STORAGE_ERRORS: dict[type[Exception], tuple[int, str, str]] = {
    InvalidFileIdError: (404, "no_encontrado", "El archivo no existe."),
    StoredFileNotFoundError: (404, "no_encontrado", "El archivo no existe."),
    FileTooLargeError: (413, "archivo_demasiado_grande", "El archivo supera el tamaño permitido."),
    UnsupportedFileTypeError: (415, "tipo_no_permitido", "Tipo de archivo no permitido."),
    EmptyFileError: (400, "archivo_vacio", "El archivo está vacío."),
}


def create_app(settings: FilesSettings | None = None) -> FastAPI:
    settings = settings or FilesSettings.from_env()
    _configure_logging()
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    storage = LocalFileStorage(
        settings.storage_dir, max_bytes=settings.max_bytes, allowed_types=settings.allowed_types
    )
    expected_auth = f"Bearer {settings.service_token}".encode()

    app = FastAPI(title="APHIA Files", docs_url=None, redoc_url=None, openapi_url=None)

    async def require_service_token(
        authorization: Annotated[str | None, Header()] = None,
    ) -> None:
        provided = (authorization or "").encode()
        if not hmac.compare_digest(provided, expected_auth):
            raise ServiceError(401, "no_autorizado", "Token de servicio inválido o ausente.")

    # Todas las rutas de archivos exigen el token de servicio.
    files = APIRouter(prefix="/v1/files", dependencies=[Depends(require_service_token)])

    @app.exception_handler(ServiceError)
    async def handle_service_error(_: Request, exc: ServiceError) -> JSONResponse:
        headers = {"WWW-Authenticate": "Bearer"} if exc.status == 401 else None
        return JSONResponse(
            {"error": {"codigo": exc.code, "mensaje": exc.message}},
            status_code=exc.status,
            headers=headers,
        )

    for error_type, (status, code, message) in _STORAGE_ERRORS.items():
        app.add_exception_handler(error_type, _storage_handler(status, code, message))

    @app.middleware("http")
    async def security_headers(request: Request, call_next: Any) -> Response:
        try:
            response = await call_next(request)
        except Exception as exc:  # noqa: BLE001 - último nivel de defensa, sin filtrar detalles
            _log(logging.ERROR, "unhandled_exception", error_type=type(exc).__name__)
            response = JSONResponse(
                {"error": {"codigo": "error_interno", "mensaje": "Error interno."}},
                status_code=500,
            )
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Cache-Control", "no-store")
        response.headers.setdefault("Content-Security-Policy", "default-src 'none'; sandbox")
        return response

    @app.get("/health")
    async def health() -> JSONResponse:
        if not storage.is_writable():
            return JSONResponse({"status": "error"}, status_code=503)
        return JSONResponse({"status": "ok"})

    @files.post("", status_code=201)
    async def upload(
        request: Request,
        x_filename: Annotated[str | None, Header()] = None,
    ) -> dict[str, object]:
        content_length = request.headers.get("content-length")
        if content_length and content_length.isdigit() and int(content_length) > settings.max_bytes:
            raise FileTooLargeError()
        try:
            stored = await storage.save(
                request.stream(),
                declared_type=request.headers.get("content-type"),
                original_name=unquote(x_filename) if x_filename else None,
            )
        except (FileTooLargeError, UnsupportedFileTypeError, EmptyFileError) as exc:
            _log(logging.WARNING, "upload_rejected", reason=type(exc).__name__)
            raise
        _log(logging.INFO, "file_stored", file_id=stored.id, size=stored.size)
        return stored.to_dict()

    @files.get("/{file_id}/metadata")
    async def metadata(file_id: str) -> dict[str, object]:
        return storage.metadata(file_id).to_dict()

    @files.get("/{file_id}")
    async def download(file_id: str) -> FileResponse:
        stored = storage.metadata(file_id)
        path = storage.content_path(file_id)
        filename = stored.original_name or f"{stored.id}"
        return FileResponse(
            path,
            media_type=stored.content_type,
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}",
                "X-File-Sha256": stored.sha256,
            },
        )

    @files.delete("/{file_id}", status_code=204)
    async def delete(file_id: str) -> Response:
        storage.delete(file_id)
        _log(logging.INFO, "file_deleted", file_id=file_id)
        return Response(status_code=204)

    app.include_router(files)
    return app


def _storage_handler(status: int, code: str, message: str) -> Any:
    async def handler(_: Request, __: Exception) -> JSONResponse:
        return JSONResponse({"error": {"codigo": code, "mensaje": message}}, status_code=status)

    return handler


def _configure_logging() -> None:
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
