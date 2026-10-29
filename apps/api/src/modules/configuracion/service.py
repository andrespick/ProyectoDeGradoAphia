from __future__ import annotations

from typing import Protocol

from core.errors import AppError
from modules.configuracion.schemas import Empresa, PoliticaSeguridad


class ClaveInseguraError(AppError):
    status_code = 422
    code = "clave_insegura"

    def __init__(self, mensaje: str, campo: str = "clave") -> None:
        super().__init__(mensaje)
        self.details = [
            {"campo": campo, "ubicacion": "body", "mensaje": mensaje, "tipo": self.code}
        ]


class ConfiguracionRepositoryPort(Protocol):
    async def obtener_politica(self) -> PoliticaSeguridad: ...

    async def guardar_politica(self, politica: PoliticaSeguridad) -> PoliticaSeguridad: ...

    async def obtener_empresa(self) -> Empresa: ...

    async def guardar_empresa(self, empresa: Empresa) -> Empresa: ...


def exigir_clave_segura(clave: str, politica: PoliticaSeguridad, campo: str = "clave") -> None:
    """El esquema ya exige 8 caracteres con letra y dígito; aquí se aplica el largo vigente."""
    if len(clave) < politica.largo_minimo_clave:
        raise ClaveInseguraError(
            f"La clave debe tener al menos {politica.largo_minimo_clave} caracteres.", campo
        )
