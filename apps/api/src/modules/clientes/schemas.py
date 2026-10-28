from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.text import normalizar_correo, normalizar_nombre


class ClienteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    nombre: str = Field(min_length=2, max_length=150)
    correo: str = Field(min_length=3, max_length=254)

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, value: str) -> str:
        return normalizar_nombre(value)

    @field_validator("correo")
    @classmethod
    def validar_correo(cls, value: str) -> str:
        return normalizar_correo(value)


class Cliente(BaseModel):
    id: int
    nombre: str
    correo: str
    creado_en: datetime
    actualizado_en: datetime

    @field_validator("creado_en", "actualizado_en")
    @classmethod
    def en_utc(cls, value: datetime) -> datetime:
        # MySQL DATETIME no guarda zona horaria; la sesión usa UTC (+00:00).
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value


class ClientesPage(BaseModel):
    items: list[Cliente]
    total: int
    limit: int
    offset: int
