from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel


class Role(StrEnum):
    ADMIN = "admin"
    ASESOR = "asesor"
    CONSULTA = "consulta"


class Principal(BaseModel):
    """Identidad de quien hace la solicitud."""

    sujeto: str
    nombre: str
    roles: list[Role]
    modo: Literal["development"]
