"""Conexiones MySQL con aiomysql.

Cada operación abre y cierra su conexión de forma explícita:

- En Cloudflare Workers los sockets no pueden reutilizarse entre solicitudes y
  Hyperdrive ya mantiene el pool de conexiones hacia MySQL.
- En Uvicorn el volumen de APHIA es bajo; si crece, aquí se puede añadir un pool
  sin cambiar los repositorios.

Las consultas siempre usan parámetros (``%s``); nunca se interpolan valores en el SQL.
"""

from __future__ import annotations

import logging
import ssl
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

import aiomysql
import pymysql

from core.errors import DatabaseNotConfiguredError, DatabaseUnavailableError
from core.logging import get_logger, log_event
from db.config import DatabaseConfig

logger = get_logger("db")

_CONNECTION_ERRORS = (
    pymysql.err.OperationalError,
    pymysql.err.InterfaceError,
    OSError,
    TimeoutError,
)


def _tls_context() -> ssl.SSLContext:
    # MySQL usa un certificado autofirmado y solo es accesible en la red interna de Docker:
    # se cifra el tráfico sin validar la cadena (igual que database/scripts/dbscripts.py).
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


class Database:
    def __init__(self, config: DatabaseConfig | None) -> None:
        self._config = config

    @asynccontextmanager
    async def connection(self) -> AsyncIterator[aiomysql.Connection]:
        if self._config is None:
            raise DatabaseNotConfiguredError()
        config = self._config
        try:
            conn = await aiomysql.connect(
                host=config.host,
                port=config.port,
                user=config.user,
                password=config.password,
                db=config.database,
                charset="utf8mb4",
                autocommit=False,
                connect_timeout=config.connect_timeout,
                init_command="SET time_zone = '+00:00'",
                ssl=_tls_context() if config.ssl_required else None,
            )
        except _CONNECTION_ERRORS as exc:
            log_event(logger, logging.WARNING, "db_connect_failed", error_type=type(exc).__name__)
            raise DatabaseUnavailableError() from exc

        try:
            yield conn
        except _CONNECTION_ERRORS as exc:
            log_event(logger, logging.WARNING, "db_operation_failed", error_type=type(exc).__name__)
            raise DatabaseUnavailableError() from exc
        finally:
            conn.close()

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[aiomysql.Connection]:
        """Confirma al salir sin errores; revierte ante cualquier excepción."""
        async with self.connection() as conn:
            try:
                yield conn
            except BaseException:
                with suppress(*_CONNECTION_ERRORS):
                    await conn.rollback()
                raise
            await conn.commit()

    async def ping(self) -> None:
        async with self.connection() as conn, conn.cursor() as cursor:
            await cursor.execute("SELECT 1")
            await cursor.fetchone()
