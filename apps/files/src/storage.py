"""Almacenamiento local de documentos en un volumen persistente.

Estructura en disco (nunca se usa el nombre original del archivo como ruta)::

    <raíz>/<2 primeros caracteres del id>/<id>.bin   contenido
    <raíz>/<2 primeros caracteres del id>/<id>.json  metadatos

- El id es un UUID4 en hexadecimal (32 caracteres) generado por el servicio.
- Los archivos se crean en modo exclusivo (``xb``): jamás se sobrescribe uno existente.
- El tipo se valida por la firma de los primeros bytes, no por la extensión ni por la
  cabecera ``Content-Type`` enviada.
- Un archivo solo es visible cuando sus metadatos existen; los metadatos se escriben de
  forma atómica al final de la subida.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
import uuid
from collections.abc import AsyncIterator
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

FILE_ID_RE = re.compile(r"^[0-9a-f]{32}$")
SIGNATURE_BYTES = 8

_SIGNATURES: dict[str, tuple[bytes, ...]] = {
    "application/pdf": (b"%PDF-",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "image/jpeg": (b"\xff\xd8\xff",),
}


class StorageError(Exception):
    pass


class InvalidFileIdError(StorageError):
    pass


class StoredFileNotFoundError(StorageError):
    pass


class FileTooLargeError(StorageError):
    pass


class UnsupportedFileTypeError(StorageError):
    pass


class EmptyFileError(StorageError):
    pass


@dataclass(frozen=True, slots=True)
class StoredFile:
    id: str
    content_type: str
    size: int
    sha256: str
    original_name: str | None
    created_at: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def detect_content_type(head: bytes) -> str | None:
    for content_type, signatures in _SIGNATURES.items():
        if any(head.startswith(signature) for signature in signatures):
            return content_type
    return None


def sanitize_filename(name: str | None) -> str | None:
    """Nombre original solo como metadato: sin rutas, sin caracteres de control, ≤ 200."""
    if not name:
        return None
    base = name.replace("\\", "/").rsplit("/", 1)[-1]
    cleaned = "".join(ch for ch in base if not unicodedata.category(ch).startswith("C")).strip()
    cleaned = cleaned.strip(".")
    return cleaned[:200] or None


class LocalFileStorage:
    def __init__(self, root: Path, *, max_bytes: int, allowed_types: frozenset[str]) -> None:
        self.root = root.resolve()
        self.max_bytes = max_bytes
        self.allowed_types = allowed_types

    def is_writable(self) -> bool:
        return self.root.is_dir() and os.access(self.root, os.W_OK)

    def _paths(self, file_id: str) -> tuple[Path, Path]:
        if not FILE_ID_RE.fullmatch(file_id):
            raise InvalidFileIdError()
        directory = (self.root / file_id[:2]).resolve()
        if not directory.is_relative_to(self.root):  # defensa adicional ante path traversal
            raise InvalidFileIdError()
        return directory / f"{file_id}.bin", directory / f"{file_id}.json"

    async def save(
        self,
        chunks: AsyncIterator[bytes],
        *,
        declared_type: str | None,
        original_name: str | None,
    ) -> StoredFile:
        file_id = uuid.uuid4().hex
        data_path, meta_path = self._paths(file_id)
        data_path.parent.mkdir(parents=True, exist_ok=True)

        digest = hashlib.sha256()
        size = 0
        head = b""
        content_type: str | None = None
        completed = False
        try:
            with data_path.open("xb") as output:
                async for chunk in chunks:
                    if not chunk:
                        continue
                    size += len(chunk)
                    if size > self.max_bytes:
                        raise FileTooLargeError()
                    if content_type is None:
                        head = (head + chunk)[:SIGNATURE_BYTES]
                        if len(head) >= SIGNATURE_BYTES:
                            content_type = self._validate_type(head, declared_type)
                    digest.update(chunk)
                    output.write(chunk)
            if size == 0:
                raise EmptyFileError()
            if content_type is None:  # archivo más corto que la firma completa
                content_type = self._validate_type(head, declared_type)

            stored = StoredFile(
                id=file_id,
                content_type=content_type,
                size=size,
                sha256=digest.hexdigest(),
                original_name=sanitize_filename(original_name),
                created_at=datetime.now(UTC).isoformat(),
            )
            tmp_meta = meta_path.with_suffix(".json.tmp")
            with tmp_meta.open("x", encoding="utf-8") as meta_file:
                json.dump(stored.to_dict(), meta_file, ensure_ascii=False)
            os.replace(tmp_meta, meta_path)
            completed = True
            return stored
        finally:
            if not completed:
                data_path.unlink(missing_ok=True)

    def _validate_type(self, head: bytes, declared_type: str | None) -> str:
        detected = detect_content_type(head)
        if detected is None or detected not in self.allowed_types:
            raise UnsupportedFileTypeError()
        declared = (declared_type or "").split(";", 1)[0].strip().lower()
        if declared and declared != "application/octet-stream" and declared != detected:
            raise UnsupportedFileTypeError()
        return detected

    def metadata(self, file_id: str) -> StoredFile:
        _, meta_path = self._paths(file_id)
        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise StoredFileNotFoundError() from exc
        return StoredFile(**data)

    def content_path(self, file_id: str) -> Path:
        self.metadata(file_id)
        data_path, _ = self._paths(file_id)
        if not data_path.is_file():
            raise StoredFileNotFoundError()
        return data_path

    def delete(self, file_id: str) -> None:
        data_path, meta_path = self._paths(file_id)
        if not meta_path.exists():
            raise StoredFileNotFoundError()
        # Primero los metadatos: el archivo deja de ser visible aunque falle el resto.
        meta_path.unlink()
        data_path.unlink(missing_ok=True)
