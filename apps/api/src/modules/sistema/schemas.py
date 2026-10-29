from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

EstadoRespaldo = Literal["solicitado", "en_curso", "ok", "fallido"]
# Un respaldo diario: más de 26 horas sin uno exitoso indica que el cron no está corriendo.
HORAS_RESPALDO_ATRASADO = 26


class Respaldo(BaseModel):
    id: int
    origen: Literal["programado", "manual"]
    estado: EstadoRespaldo
    solicitado_en: datetime
    iniciado_en: datetime | None
    terminado_en: datetime | None
    archivo: str | None
    tamano_bytes: int | None
    copia_externa: bool | None
    error: str | None


class RespaldosPage(BaseModel):
    items: list[Respaldo]
    total: int
    limit: int
    offset: int


class EstadoApi(BaseModel):
    version: str
    entorno: str
    runtime: Literal["workers", "asgi"]


class EstadoBaseDatos(BaseModel):
    disponible: bool
    latencia_ms: float | None = None
    version: str | None = None
    tamano_bytes: int | None = None


class EstadoMigraciones(BaseModel):
    aplicadas: int
    ultima: str | None
    aplicada_en: datetime | None


class ConteoRegistros(BaseModel):
    personas: int
    inmuebles: int
    contratos: int
    usuarios: int
    eventos_auditoria: int
    en_papelera: int


class EstadoRespaldos(BaseModel):
    ultimo_exitoso: Respaldo | None
    pendiente: Respaldo | None
    atrasado: bool


class EstadoSistema(BaseModel):
    api: EstadoApi
    base_de_datos: EstadoBaseDatos
    # None cuando la base de datos no responde.
    migraciones: EstadoMigraciones | None = None
    registros: ConteoRegistros | None = None
    respaldos: EstadoRespaldos | None = None


@dataclass(frozen=True)
class Diagnostico:
    base_de_datos: EstadoBaseDatos
    migraciones: EstadoMigraciones
    registros: ConteoRegistros
    ultimo_exitoso: Respaldo | None
    pendiente: Respaldo | None
