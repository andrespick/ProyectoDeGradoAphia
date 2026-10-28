"""Utilidades SQL compartidas por los repositorios (sin conexión ni estado)."""

from __future__ import annotations

ER_DUP_ENTRY = 1062
ER_ROW_IS_REFERENCED = 1451
ER_NO_REFERENCED_ROW = 1452


def mysql_error_code(exc: BaseException) -> int | None:
    """Código numérico de un error de MySQL/pymysql; ``None`` si no lo trae."""
    args = getattr(exc, "args", ())
    return args[0] if args and isinstance(args[0], int) else None


def like_pattern(text: str) -> str:
    """Patrón ``%texto%`` para ``LIKE`` con los comodines del usuario escapados."""
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"
