from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.text import normalizar_nombre

# Papel de una persona: código del catálogo ``party_role`` ↔ nombre que expone la API.
PAPEL_POR_CODIGO = {"OWNER": "propietario", "TENANT": "arrendatario", "CO_DEBTOR": "codeudor"}
CODIGO_POR_PAPEL = {papel: codigo for codigo, papel in PAPEL_POR_CODIGO.items()}


class Opcion(BaseModel):
    codigo: str
    nombre: str


class Ciudad(BaseModel):
    id: int
    nombre: str


class Catalogos(BaseModel):
    tipos_identificacion: list[Opcion]
    papeles: list[Opcion]
    roles: list[Opcion]
    estados_ocupacion: list[Opcion]
    tipos_contrato: list[Opcion]
    tipos_cuenta_bancaria: list[Opcion]
    tipos_servicio: list[Opcion]
    monedas: list[Opcion]
    ciudades: list[Ciudad]
    bancos: list[str]
    proveedores_servicios: list[str]


# Catálogos que el Administrador de Sistemas mantiene desde la web. Papeles, roles, estados de
# ocupación y monedas no están: la aplicación depende de sus códigos.
CatalogoAdministrable = Literal[
    "tipos-identificacion",
    "tipos-contrato",
    "tipos-cuenta-bancaria",
    "tipos-servicio",
    "ciudades",
    "bancos",
    "proveedores-servicios",
]


class ItemCatalogo(BaseModel):
    id: int
    codigo: str | None
    nombre: str
    # Registros que lo usan; si es mayor que cero no se puede eliminar.
    en_uso: int


class ItemCatalogoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    nombre: str = Field(min_length=1, max_length=255)

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, value: str) -> str:
        return normalizar_nombre(value)


class ItemCatalogoCreate(ItemCatalogoUpdate):
    # Obligatorio en los catálogos con código; se ignora en ciudades, bancos y proveedores.
    codigo: str | None = Field(
        default=None, min_length=1, max_length=30, pattern=r"^[A-Za-z0-9_]+$"
    )

    @field_validator("codigo")
    @classmethod
    def mayusculas(cls, value: str | None) -> str | None:
        return None if value is None else value.upper()
