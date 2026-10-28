"""Registro de eventos en formato JSON (una línea por evento).

Reglas: no registrar contraseñas, tokens, cuerpos de solicitudes, cadenas de conexión
ni datos personales. Registrar identificadores técnicos (request_id, códigos de error).
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

ROOT_LOGGER = "aphia"


class _StdoutHandler(logging.Handler):
    """Escribe en el ``sys.stdout`` vigente (Workers reenvía stdout a sus logs)."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            sys.stdout.write(self.format(record) + "\n")
        except Exception:  # noqa: BLE001 - el logging nunca debe romper una solicitud
            self.handleError(record)


def configure_logging(level: str = "INFO") -> None:
    logger = logging.getLogger(ROOT_LOGGER)
    if not any(isinstance(h, _StdoutHandler) for h in logger.handlers):
        handler = _StdoutHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
        logger.propagate = False
    level = level.upper()
    logger.setLevel(level if level in logging.getLevelNamesMapping() else "INFO")


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"{ROOT_LOGGER}.{name}")


def log_event(logger: logging.Logger, level: int, event: str, **fields: Any) -> None:
    if logger.isEnabledFor(level):
        payload = {"level": logging.getLevelName(level), "event": event, **fields}
        logger.log(level, json.dumps(payload, ensure_ascii=False, default=str))
