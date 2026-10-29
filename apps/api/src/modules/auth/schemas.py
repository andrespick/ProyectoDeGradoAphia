from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Role(StrEnum):
    """Roles de acceso. El valor es el que viaja en la API; ``code`` es el de ``app_role``."""

    ADMIN_SISTEMAS = "admin_sistemas"
    ADMINISTRATIVO = "administrativo"
    ASESOR = "asesor"

    @classmethod
    def from_code(cls, code: str) -> Role:
        return cls(code.lower())

    @property
    def code(self) -> str:
        return self.value.upper()


# Grupos de permisos (decisión con el responsable: el asesor crea y edita, pero no elimina;
# el administrador de sistemas solo gestiona el sistema, no los módulos de negocio).
LECTURA = (Role.ADMINISTRATIVO, Role.ASESOR)
ESCRITURA = LECTURA
ELIMINACION = (Role.ADMINISTRATIVO,)
GESTION_SISTEMA = (Role.ADMIN_SISTEMAS,)
TODOS = tuple(Role)


class Principal(BaseModel):
    """Identidad de quien hace la solicitud."""

    sujeto: str
    nombre: str
    roles: list[Role]
    modo: Literal["development", "database"]
    # Tras un restablecimiento: solo puede consultar /auth/me y cambiar su contraseña.
    debe_cambiar_clave: bool = False


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    usuario: str = Field(min_length=1, max_length=255)
    # La clave no se recorta: los espacios pueden ser parte de ella.
    clave: str = Field(min_length=1, max_length=128)

    @field_validator("usuario")
    @classmethod
    def recortar_usuario(cls, value: str) -> str:
        return value.strip()


class CambioClaveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    clave_actual: str = Field(min_length=1, max_length=128)
    clave_nueva: str = Field(min_length=8, max_length=128)

    @field_validator("clave_nueva")
    @classmethod
    def clave_segura(cls, value: str) -> str:
        return validar_clave(value)


def validar_clave(value: str) -> str:
    if not any(c.isalpha() for c in value) or not any(c.isdigit() for c in value):
        raise ValueError("La clave debe tener al menos una letra y un dígito")
    return value


class LoginResponse(BaseModel):
    token: str
    expira_en: datetime
    principal: Principal
