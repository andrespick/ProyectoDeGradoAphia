from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_ALLOWED_TYPES = "application/pdf,image/png,image/jpeg"
MIN_TOKEN_LENGTH = 32


class ConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class FilesSettings:
    storage_dir: Path
    service_token: str = field(repr=False)
    max_bytes: int = 10 * 1024 * 1024
    allowed_types: frozenset[str] = frozenset(DEFAULT_ALLOWED_TYPES.split(","))

    def __post_init__(self) -> None:
        token = self.service_token
        if len(token) < MIN_TOKEN_LENGTH or "change-me" in token.lower():
            raise ConfigurationError(
                f"FILES_SERVICE_TOKEN debe tener al menos {MIN_TOKEN_LENGTH} caracteres aleatorios."
            )
        if self.max_bytes <= 0:
            raise ConfigurationError("FILES_MAX_BYTES debe ser mayor que cero.")

    @classmethod
    def from_env(cls, environ: Mapping[str, str] = os.environ) -> FilesSettings:
        return cls(
            storage_dir=Path(environ.get("FILES_STORAGE_DIR", "/data")),
            service_token=_read_secret(environ, "FILES_SERVICE_TOKEN"),
            max_bytes=int(environ.get("FILES_MAX_BYTES", str(10 * 1024 * 1024))),
            allowed_types=frozenset(
                item.strip().lower()
                for item in environ.get("FILES_ALLOWED_TYPES", DEFAULT_ALLOWED_TYPES).split(",")
                if item.strip()
            ),
        )


def _read_secret(environ: Mapping[str, str], name: str) -> str:
    """Admite ``NOMBRE`` o ``NOMBRE_FILE`` (Docker secrets)."""
    file_path = environ.get(f"{name}_FILE")
    if file_path:
        return Path(file_path).read_text(encoding="utf-8").strip()
    return environ.get(name, "")
