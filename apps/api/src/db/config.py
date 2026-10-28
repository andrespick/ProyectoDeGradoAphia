from __future__ import annotations

from dataclasses import dataclass, field

from core.config import Settings


@dataclass(frozen=True, slots=True)
class DatabaseConfig:
    host: str
    port: int
    user: str
    password: str = field(repr=False)
    database: str
    connect_timeout: int = 5

    @classmethod
    def from_settings(cls, settings: Settings) -> DatabaseConfig | None:
        """Configuración para Uvicorn (variables ``DB_*``). ``None`` si está incompleta."""
        if not (settings.db_host and settings.db_name and settings.db_user):
            return None
        if settings.db_password is None:
            return None
        return cls(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            database=settings.db_name,
            connect_timeout=settings.db_connect_timeout,
        )
