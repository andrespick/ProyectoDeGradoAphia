from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from core.text import vacio_a_none
from modules.personas.schemas import InmuebleResumen, PersonaResumen

EstadoContrato = Literal["programado", "vigente", "finalizado"]
DIAS_POR_VENCER = 60
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class ContratoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    tipo: str = Field(min_length=1, max_length=30)
    inmueble_id: int = Field(ge=1)
    fecha_inicio: date
    fecha_fin: date | None = None
    canon_pactado: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    condiciones: str | None = Field(default=None, max_length=20_000)
    texto: str | None = Field(default=None, max_length=1_000_000)
    # None = los propietarios actuales del inmueble (property_owner); [] se rechaza.
    propietarios_ids: list[int] | None = Field(default=None, min_length=1, max_length=20)
    arrendatario_id: int | None = Field(default=None, ge=1)
    codeudores_ids: list[int] = Field(default_factory=list, max_length=10)

    @field_validator("condiciones", "texto", mode="before")
    @classmethod
    def blancos_a_none(cls, value: object) -> object:
        return vacio_a_none(value)

    @field_validator("condiciones", "texto")
    @classmethod
    def sin_caracteres_de_control(cls, value: str | None) -> str | None:
        if value is not None and _CONTROL_RE.search(value):
            raise ValueError("El texto contiene caracteres no permitidos.")
        return value

    @field_validator("tipo")
    @classmethod
    def mayusculas(cls, value: str) -> str:
        return value.upper()

    @field_validator("propietarios_ids", "codeudores_ids")
    @classmethod
    def sin_duplicados(cls, value: list[int] | None) -> list[int] | None:
        return None if value is None else list(dict.fromkeys(value))

    @model_validator(mode="after")
    def coherencia(self) -> ContratoCreate:
        if self.fecha_fin is not None and self.fecha_fin < self.fecha_inicio:
            raise ValueError("La fecha de fin no puede ser anterior a la de inicio.")
        if self.arrendatario_id is not None and self.arrendatario_id in self.codeudores_ids:
            raise ValueError("El arrendatario no puede ser también codeudor del contrato.")
        return self


ContratoUpdate = ContratoCreate


class ContratoListado(BaseModel):
    id: int
    tipo: str
    inmueble: InmuebleResumen
    fecha_inicio: date
    fecha_fin: date | None
    canon_pactado: Decimal | None
    moneda: str | None
    estado: EstadoContrato
    dias_restantes: int | None
    propietarios: list[PersonaResumen]
    arrendatario: PersonaResumen | None
    codeudores: list[PersonaResumen]


class Contrato(ContratoListado):
    condiciones: str | None
    texto: str | None


class ContratosPage(BaseModel):
    items: list[ContratoListado]
    total: int
    limit: int
    offset: int


@dataclass(frozen=True)
class ContratoFiltros:
    fecha_desde: date | None = None
    fecha_hasta: date | None = None
    inmueble_id: int | None = None
    propietario_id: int | None = None
    inquilino_id: int | None = None
    tipo: str | None = None
    estado: str | None = None
    q: str | None = None


def estado_de(inicio: date, fin: date | None, hoy: date) -> tuple[EstadoContrato, int | None]:
    """Estado calculado y días restantes (None si es indefinido)."""
    if fin is not None and fin < hoy:
        return "finalizado", 0
    if inicio > hoy:
        return "programado", None if fin is None else (fin - hoy).days
    return "vigente", None if fin is None else (fin - hoy).days
