"""Fecha de negocio. La empresa opera en Colombia: UTC-5 todo el año (sin horario de verano).

MySQL y la API trabajan en UTC (``SET time_zone = '+00:00'``), pero «hoy» para un contrato es
el día de Colombia: entre las 7:00 p. m. y la medianoche la fecha UTC ya es la de mañana.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta, timezone

HORAS_DETRAS_DE_UTC = 5
COLOMBIA = timezone(timedelta(hours=-HORAS_DETRAS_DE_UTC))


def hoy(ahora: datetime | None = None) -> date:
    return (ahora or datetime.now(UTC)).astimezone(COLOMBIA).date()


def inicio_del_dia_utc(dia: date) -> datetime:
    """Medianoche de Colombia de ``dia`` en UTC sin zona, como se guardan los DATETIME."""
    return datetime.combine(dia, time(), COLOMBIA).astimezone(UTC).replace(tzinfo=None)
