# ruff: noqa: S608 - el SQL se arma solo con fragmentos fijos (HOY_SQL es una constante)
from __future__ import annotations

from typing import Any, Protocol

import aiomysql

from db.connection import Database
from db.sql import HOY_SQL
from modules.resumen.schemas import (
    Resumen,
    ResumenContratos,
    ResumenInmuebles,
    ResumenPersonas,
    ResumenUsuarios,
)

_PERSONAS = (
    "SELECT COUNT(DISTINCT ppr.person_id) AS total, "
    "COUNT(DISTINCT CASE WHEN pr.code = 'OWNER' THEN ppr.person_id END) AS propietarios, "
    "COUNT(DISTINCT CASE WHEN pr.code = 'TENANT' THEN ppr.person_id END) AS arrendatarios, "
    "COUNT(DISTINCT CASE WHEN pr.code = 'CO_DEBTOR' THEN ppr.person_id END) AS codeudores "
    "FROM person_party_role ppr JOIN party_role pr ON pr.party_role_id = ppr.party_role_id"
)
_INMUEBLES = (
    "SELECT COUNT(*) AS total, "
    "COALESCE(SUM(os.code = 'OCUPADO'), 0) AS ocupados, "
    "COALESCE(SUM(os.code = 'DISPONIBLE'), 0) AS disponibles "
    "FROM property p LEFT JOIN occupancy_state os ON os.occupancy_state_id = p.occupancy_state_id"
)
_CONTRATOS = (
    "SELECT COUNT(*) AS total, "
    f"COALESCE(SUM(start_date <= {HOY_SQL} AND (end_date IS NULL OR end_date >= {HOY_SQL})), 0) "
    " AS vigentes, "
    f"COALESCE(SUM(end_date BETWEEN {HOY_SQL} AND {HOY_SQL} + INTERVAL 30 DAY), 0) "
    " AS por_vencer_30, "
    f"COALESCE(SUM(end_date BETWEEN {HOY_SQL} AND {HOY_SQL} + INTERVAL 60 DAY), 0) "
    " AS por_vencer_60, "
    f"COALESCE(SUM(end_date < {HOY_SQL}), 0) AS finalizados "
    "FROM property_agreement"
)
_CODEUDORES = (
    "SELECT COUNT(*) AS codeudores_vinculados FROM agreement_party ap "
    "JOIN party_role pr ON pr.party_role_id = ap.party_role_id WHERE pr.code = 'CO_DEBTOR'"
)
_USUARIOS = (
    "SELECT COUNT(*) AS total, "
    "COALESCE(SUM(is_active = 1 AND (locked_until IS NULL OR locked_until <= UTC_TIMESTAMP(6))), "
    " 0) "
    " AS activos, "
    "COALESCE(SUM(locked_until > UTC_TIMESTAMP(6)), 0) AS bloqueados "
    "FROM user_account"
)


class ResumenRepositoryPort(Protocol):
    async def obtener(self) -> Resumen: ...


class ResumenRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def obtener(self) -> Resumen:
        async with self._db.connection() as conn, conn.cursor(aiomysql.DictCursor) as cursor:
            personas = await _row(cursor, _PERSONAS)
            inmuebles = await _row(cursor, _INMUEBLES)
            contratos = {**await _row(cursor, _CONTRATOS), **await _row(cursor, _CODEUDORES)}
            usuarios = await _row(cursor, _USUARIOS)
        return Resumen(
            personas=ResumenPersonas(**personas),
            inmuebles=ResumenInmuebles(**inmuebles),
            contratos=ResumenContratos(**contratos),
            usuarios=ResumenUsuarios(**usuarios),
        )


async def _row(cursor: aiomysql.DictCursor, sql: str) -> dict[str, Any]:
    await cursor.execute(sql)
    row = await cursor.fetchone()
    return {key: int(value) for key, value in row.items()}
