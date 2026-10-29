from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.text import normalizar_correo, normalizar_nombre, vacio_a_none


class PoliticaSeguridad(BaseModel):
    """Los límites repiten los CHECK de ``security_policy`` para responder 422 y no 500."""

    model_config = ConfigDict(extra="forbid")

    max_intentos: int = Field(ge=3, le=10)
    minutos_bloqueo: int = Field(ge=5, le=1440)
    horas_sesion: int = Field(ge=1, le=24)
    largo_minimo_clave: int = Field(ge=8, le=64)


# Valores del requisito original (los mismos que inserta la migración 0018).
POLITICA_INICIAL = PoliticaSeguridad(
    max_intentos=3, minutos_bloqueo=15, horas_sesion=8, largo_minimo_clave=8
)


class PoliticaPublica(BaseModel):
    """Lo que la pantalla de inicio de sesión muestra antes de autenticarse."""

    max_intentos: int
    minutos_bloqueo: int
    largo_minimo_clave: int


class Empresa(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    nombre: str = Field(min_length=2, max_length=255)
    nit: str | None = Field(default=None, min_length=5, max_length=50, pattern=r"^[0-9.-]+$")
    direccion: str | None = Field(default=None, min_length=3, max_length=255)
    ciudad: str | None = Field(default=None, min_length=1, max_length=255)
    telefono: str | None = Field(
        default=None, min_length=7, max_length=50, pattern=r"^[0-9+ ()-]+$"
    )
    correo: str | None = Field(default=None, min_length=3, max_length=254)

    @field_validator("nit", "direccion", "ciudad", "telefono", "correo", mode="before")
    @classmethod
    def blancos_a_none(cls, value: object) -> object:
        return vacio_a_none(value)

    @field_validator("nombre", "ciudad")
    @classmethod
    def validar_nombre(cls, value: str | None) -> str | None:
        return None if value is None else normalizar_nombre(value)

    @field_validator("correo")
    @classmethod
    def validar_correo(cls, value: str | None) -> str | None:
        return None if value is None else normalizar_correo(value)
