from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel


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


# Grupos de permisos (decisión con el responsable: el asesor crea y edita, pero no elimina).
LECTURA = (Role.ADMIN_SISTEMAS, Role.ADMINISTRATIVO, Role.ASESOR)
ESCRITURA = LECTURA
ELIMINACION = (Role.ADMIN_SISTEMAS, Role.ADMINISTRATIVO)
GESTION_USUARIOS = (Role.ADMIN_SISTEMAS,)


class Principal(BaseModel):
    """Identidad de quien hace la solicitud."""

    sujeto: str
    nombre: str
    roles: list[Role]
    modo: Literal["development", "database"]
