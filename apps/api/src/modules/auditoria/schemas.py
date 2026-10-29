from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from pydantic import BaseModel


@dataclass(frozen=True)
class NuevoEvento:
    accion: str
    entidad: str | None = None
    entidad_id: int | None = None
    detalle: str | None = None
    actor_id: int | None = None
    actor_nombre: str | None = None
    request_id: str | None = None


class EventoAuditoria(BaseModel):
    id: int
    fecha: datetime
    actor_id: int | None
    actor_nombre: str | None
    # Nombre de usuario actual de la cuenta (None si la cuenta ya no existe).
    actor_usuario: str | None
    accion: str
    entidad: str | None
    entidad_id: int | None
    detalle: str | None
    request_id: str | None


class AuditoriaPage(BaseModel):
    items: list[EventoAuditoria]
    total: int
    limit: int
    offset: int


@dataclass(frozen=True)
class AuditoriaFiltros:
    accion: str | None = None
    entidad: str | None = None
    entidad_id: int | None = None
    q: str | None = None
    desde: date | None = None
    hasta: date | None = None
