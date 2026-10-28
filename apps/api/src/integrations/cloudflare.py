"""Adaptador del runtime de Cloudflare Workers.

Es el único módulo de la API que conoce los bindings de Workers (variables, secretos e
Hyperdrive). No importa el paquete ``workers``: solo lee atributos del objeto ``env``
que el runtime coloca en ``scope["env"]``, de modo que la aplicación sigue funcionando
con Uvicorn, donde ese objeto no existe.
"""

from __future__ import annotations

from typing import Any

from starlette.types import Scope

from core.config import Getter
from db.config import DatabaseConfig

HYPERDRIVE_BINDING = "HYPERDRIVE"


def worker_env(scope: Scope) -> Any | None:
    return scope.get("env")


def env_getter(env: Any) -> Getter:
    def get(name: str) -> str | None:
        value = getattr(env, name, None)
        return None if value is None else str(value)

    return get


def hyperdrive_config(env: Any, binding: str = HYPERDRIVE_BINDING) -> DatabaseConfig | None:
    """Parámetros de conexión que Hyperdrive expone en el binding (ver docs de Hyperdrive)."""
    hyperdrive = getattr(env, binding, None)
    if hyperdrive is None:
        return None
    return DatabaseConfig(
        host=str(hyperdrive.host),
        port=int(hyperdrive.port),
        user=str(hyperdrive.user),
        password=str(hyperdrive.password),
        database=str(hyperdrive.database),
    )
