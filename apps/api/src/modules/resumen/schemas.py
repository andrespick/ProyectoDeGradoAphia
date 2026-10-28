from __future__ import annotations

from pydantic import BaseModel


class ResumenPersonas(BaseModel):
    total: int
    propietarios: int
    arrendatarios: int
    codeudores: int


class ResumenInmuebles(BaseModel):
    total: int
    ocupados: int
    disponibles: int


class ResumenContratos(BaseModel):
    total: int
    vigentes: int
    por_vencer_30: int
    por_vencer_60: int
    finalizados: int
    codeudores_vinculados: int


class ResumenUsuarios(BaseModel):
    total: int
    activos: int
    bloqueados: int


class Resumen(BaseModel):
    personas: ResumenPersonas
    inmuebles: ResumenInmuebles
    contratos: ResumenContratos
    usuarios: ResumenUsuarios
