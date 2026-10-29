from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.text import normalizar_correo, normalizar_nombre, vacio_a_none
from modules.catalogos.schemas import CODIGO_POR_PAPEL

Papel = Literal["propietario", "arrendatario", "codeudor"]
PAPELES: tuple[Papel, ...] = ("propietario", "arrendatario", "codeudor")


class CuentaBancariaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    banco: str = Field(min_length=1, max_length=255)
    tipo: str = Field(min_length=1, max_length=30)
    numero: str = Field(min_length=1, max_length=50, pattern=r"^[0-9-]+$")

    @field_validator("tipo")
    @classmethod
    def mayusculas(cls, value: str) -> str:
        return value.upper()


class CuentaBancaria(CuentaBancariaCreate):
    id: int


class PersonaBase(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    nombre: str = Field(min_length=2, max_length=255)
    tipo_identificacion: str = Field(min_length=1, max_length=20)
    identificacion: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9-]+$")
    telefono: str | None = Field(
        default=None, min_length=7, max_length=50, pattern=r"^[0-9+ ()-]+$"
    )
    correo: str | None = Field(default=None, min_length=3, max_length=254)
    direccion: str | None = Field(default=None, min_length=1, max_length=255)

    @field_validator("telefono", "correo", "direccion", mode="before")
    @classmethod
    def blancos_a_none(cls, value: object) -> object:
        return vacio_a_none(value)

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, value: str) -> str:
        return normalizar_nombre(value)

    @field_validator("tipo_identificacion")
    @classmethod
    def mayusculas(cls, value: str) -> str:
        return value.upper()

    @field_validator("correo")
    @classmethod
    def validar_correo(cls, value: str | None) -> str | None:
        return None if value is None else normalizar_correo(value)


class PersonaCreate(PersonaBase):
    papeles: list[Papel] = Field(min_length=1)
    cuenta_bancaria: CuentaBancariaCreate | None = None

    @field_validator("papeles")
    @classmethod
    def sin_duplicados(cls, value: list[Papel]) -> list[Papel]:
        return [papel for papel in PAPELES if papel in value]


PersonaUpdate = PersonaCreate


class PersonaResumen(BaseModel):
    """Lo mínimo para mostrar una persona dentro de otro registro (inmueble, contrato)."""

    id: int
    nombre: str
    tipo_identificacion: str | None
    identificacion: str | None
    telefono: str | None
    correo: str | None


class Persona(PersonaResumen):
    direccion: str | None
    papeles: list[Papel]
    cuenta_bancaria: CuentaBancaria | None
    total_inmuebles: int


class InmuebleResumen(BaseModel):
    id: int
    direccion: str
    ciudad: str | None
    estado: str | None


class ContratoResumen(BaseModel):
    id: int
    tipo: str
    fecha_inicio: date
    fecha_fin: date | None
    inmueble: InmuebleResumen


class PersonaDetalle(Persona):
    inmuebles: list[InmuebleResumen]
    contratos_como_propietario: list[ContratoResumen]
    contratos_como_arrendatario: list[ContratoResumen]
    contratos_como_codeudor: list[ContratoResumen]
    usuario: str | None


class PersonasPage(BaseModel):
    items: list[Persona]
    total: int
    limit: int
    offset: int


@dataclass(frozen=True)
class PersonaFiltros:
    q: str | None = None
    correo: str | None = None
    papel: Papel | None = None
    contrato_id: int | None = None
    solo_con_papel: bool = False


@dataclass(frozen=True)
class Dependencias:
    inmuebles: int = 0
    contratos: int = 0
    usuarios: int = 0
    por_papel: dict[str, int] = field(default_factory=dict)


def codigo_de(papel: Papel) -> str:
    return CODIGO_POR_PAPEL[papel]
