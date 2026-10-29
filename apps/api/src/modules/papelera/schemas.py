from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

from modules.auditoria.service import actor_id_de
from modules.auth.schemas import Principal

TipoRegistro = Literal["persona", "inmueble", "contrato"]


@dataclass(frozen=True)
class EntradaPapelera:
    tipo: TipoRegistro
    entidad_id: int
    descripcion: str
    datos: dict[str, Any]
    eliminado_por_id: int | None
    eliminado_por: str | None


def entrada(
    tipo: TipoRegistro, entidad_id: int, descripcion: str, datos: dict[str, Any], actor: Principal
) -> EntradaPapelera:
    return EntradaPapelera(
        tipo=tipo,
        entidad_id=entidad_id,
        descripcion=descripcion[:255],
        datos=datos,
        eliminado_por_id=actor_id_de(actor),
        eliminado_por=actor.nombre,
    )


class RegistroEliminado(BaseModel):
    id: int
    tipo: TipoRegistro
    entidad_id: int
    descripcion: str
    eliminado_en: datetime
    eliminado_por: str | None


class PapeleraPage(BaseModel):
    items: list[RegistroEliminado]
    total: int
    limit: int
    offset: int


class Restaurado(BaseModel):
    tipo: TipoRegistro
    # Identificador nuevo del registro restaurado.
    id: int
