"""Configuración de la API.

La configuración se construye a partir de una función ``get(nombre)`` para que la
misma lógica sirva con ``os.environ`` (Uvicorn) y con el objeto ``env`` de
Cloudflare Workers, donde las variables solo existen dentro de cada solicitud.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass, field

ENVIRONMENTS = frozenset({"development", "test", "staging", "production"})
LOCAL_ENVIRONMENTS = frozenset({"development", "test"})
AUTH_MODES = frozenset({"disabled", "development"})

Getter = Callable[[str], str | None]


class ConfigurationError(RuntimeError):
    """La configuración del entorno es inválida. El mensaje nunca incluye secretos."""


@dataclass(frozen=True, slots=True)
class Settings:
    app_env: str = "development"
    cors_origins: tuple[str, ...] = ()
    auth_mode: str = "disabled"
    log_level: str = "INFO"
    db_host: str | None = None
    db_port: int = 3306
    db_name: str | None = None
    db_user: str | None = None
    db_password: str | None = field(default=None, repr=False)
    db_connect_timeout: int = 5

    @property
    def is_local(self) -> bool:
        return self.app_env in LOCAL_ENVIRONMENTS

    @classmethod
    def from_getter(cls, get: Getter) -> Settings:
        app_env = _clean(get("APP_ENV")) or "development"
        if app_env not in ENVIRONMENTS:
            raise ConfigurationError(f"APP_ENV inválido: {app_env!r}")

        auth_mode = _clean(get("AUTH_MODE")) or "disabled"
        if auth_mode not in AUTH_MODES:
            raise ConfigurationError(f"AUTH_MODE inválido: {auth_mode!r}")
        if auth_mode == "development" and app_env not in LOCAL_ENVIRONMENTS:
            raise ConfigurationError("AUTH_MODE=development solo se permite en development o test")

        return cls(
            app_env=app_env,
            cors_origins=parse_origins(get("CORS_ORIGINS")),
            auth_mode=auth_mode,
            log_level=(_clean(get("LOG_LEVEL")) or "info").upper(),
            db_host=get("DB_HOST") or None,
            db_port=_parse_int(get("DB_PORT"), "DB_PORT", 3306),
            db_name=get("DB_NAME") or None,
            db_user=get("DB_USER") or None,
            db_password=get("DB_PASSWORD"),
            db_connect_timeout=_parse_int(get("DB_CONNECT_TIMEOUT"), "DB_CONNECT_TIMEOUT", 5),
        )

    @classmethod
    def from_environ(cls) -> Settings:
        return cls.from_getter(os.environ.get)


def parse_origins(raw: str | None) -> tuple[str, ...]:
    """Convierte ``CORS_ORIGINS`` en una lista explícita. ``*`` no está permitido."""
    origins = tuple(item.strip().rstrip("/") for item in (raw or "").split(",") if item.strip())
    for origin in origins:
        if origin == "*" or not origin.startswith(("http://", "https://")):
            raise ConfigurationError(f"Origen CORS inválido: {origin!r}")
    return origins


def _clean(value: str | None) -> str:
    return (value or "").strip().lower()


def _parse_int(raw: str | None, name: str, default: int) -> int:
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigurationError(f"{name} debe ser un número entero") from exc
