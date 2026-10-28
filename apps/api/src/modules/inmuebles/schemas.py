from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from modules.personas.schemas import PersonaResumen


def _vacio_a_none(value: object) -> object:
    return None if isinstance(value, str) and not value.strip() else value


class ServicioPublicoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    tipo: str | None = Field(default=None, min_length=1, max_length=30)
    proveedor: str | None = Field(default=None, min_length=1, max_length=255)
    numero_contrato: str = Field(min_length=1, max_length=255)

    @field_validator("tipo", "proveedor", mode="before")
    @classmethod
    def vacio_a_none(cls, value: object) -> object:
        return _vacio_a_none(value)

    @field_validator("tipo")
    @classmethod
    def mayusculas(cls, value: str | None) -> str | None:
        return None if value is None else value.upper()


class ServicioPublico(ServicioPublicoCreate):
    id: int


class InmuebleCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    direccion: str = Field(min_length=3, max_length=255)
    ciudad: str | None = Field(default=None, min_length=1, max_length=255)
    matricula: str | None = Field(default=None, min_length=1, max_length=255)
    canon: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    estado: str | None = Field(default=None, min_length=1, max_length=30)
    servicios: list[ServicioPublicoCreate] = Field(default_factory=list, max_length=20)
    propietarios_ids: list[int] = Field(min_length=1, max_length=20)

    @field_validator("ciudad", "matricula", "estado", mode="before")
    @classmethod
    def vacio_a_none(cls, value: object) -> object:
        return _vacio_a_none(value)

    @field_validator("estado")
    @classmethod
    def mayusculas(cls, value: str | None) -> str | None:
        return None if value is None else value.upper()

    @field_validator("propietarios_ids")
    @classmethod
    def sin_duplicados(cls, value: list[int]) -> list[int]:
        return list(dict.fromkeys(value))


InmuebleUpdate = InmuebleCreate


class Inmueble(BaseModel):
    id: int
    direccion: str
    ciudad: str | None
    matricula: str | None
    canon: Decimal | None
    moneda: str | None
    estado: str | None
    servicios: list[ServicioPublico]
    propietarios: list[PersonaResumen]
    total_contratos: int


class InmueblesPage(BaseModel):
    items: list[Inmueble]
    total: int
    limit: int
    offset: int


@dataclass(frozen=True)
class InmuebleFiltros:
    estado: str | None = None
    ciudad: str | None = None
    propietario_id: int | None = None
    q: str | None = None
