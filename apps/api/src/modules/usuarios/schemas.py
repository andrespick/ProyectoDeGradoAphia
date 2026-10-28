from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.text import normalizar_correo, normalizar_nombre
from modules.auth.schemas import Role

EstadoUsuario = Literal["activo", "inactivo", "bloqueado"]


def validar_clave(value: str) -> str:
    if not any(c.isalpha() for c in value) or not any(c.isdigit() for c in value):
        raise ValueError("La clave debe tener al menos una letra y un dígito")
    return value


class UsuarioBase(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    nombre: str = Field(min_length=2, max_length=255)
    tipo_identificacion: str = Field(min_length=1, max_length=20)
    identificacion: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9-]+$")
    correo: str = Field(min_length=3, max_length=254)
    rol: Role
    activo: bool = True

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
    def validar_correo(cls, value: str) -> str:
        return normalizar_correo(value)


class UsuarioCreate(UsuarioBase):
    usuario: str = Field(min_length=3, max_length=50, pattern=r"^[a-z0-9._-]+$")
    clave: str = Field(min_length=8, max_length=128)

    @field_validator("clave")
    @classmethod
    def clave_segura(cls, value: str) -> str:
        return validar_clave(value)


class UsuarioUpdate(UsuarioBase):
    # None = conservar la clave actual.
    clave: str | None = Field(default=None, min_length=8, max_length=128)

    @field_validator("clave")
    @classmethod
    def clave_segura(cls, value: str | None) -> str | None:
        return None if value is None else validar_clave(value)


class Usuario(BaseModel):
    id: int
    usuario: str
    nombre: str
    tipo_identificacion: str | None
    identificacion: str | None
    correo: str | None
    rol: Role
    activo: bool
    bloqueada: bool
    bloqueada_hasta: datetime | None
    intentos_fallidos: int
    creado_en: datetime


class UsuariosPage(BaseModel):
    items: list[Usuario]
    total: int
    limit: int
    offset: int
