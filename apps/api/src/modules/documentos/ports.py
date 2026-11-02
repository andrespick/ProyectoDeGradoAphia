"""Contrato del almacenamiento de documentos usado por la lógica de negocio.

Implementación prevista: cliente HTTP hacia ``FILES_SERVICE_URL`` (red interna de Docker)
con ``Authorization: Bearer <FILES_SERVICE_TOKEN>``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class StoredDocument:
    file_id: str
    content_type: str
    size: int
    sha256: str
    original_name: str | None
    created_at: datetime


class DocumentStorage(Protocol):
    async def upload(
        self, content: bytes, content_type: str, original_name: str | None
    ) -> StoredDocument: ...

    async def download(self, file_id: str) -> tuple[StoredDocument, bytes]: ...

    async def delete(self, file_id: str) -> None: ...
