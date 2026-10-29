# ruff: noqa: S608 - el SQL se arma solo con fragmentos fijos; los valores van parametrizados
from __future__ import annotations

import json
from typing import Any

import aiomysql

from db.connection import Database
from modules.auth.repository import en_utc
from modules.papelera.schemas import EntradaPapelera, RegistroEliminado, TipoRegistro

_SELECT = (
    "SELECT deleted_record_id, entity_type, entity_id, label, deleted_at, deleted_by_name "
    "FROM deleted_record"
)


async def guardar_en_papelera(cursor: aiomysql.Cursor, entrada: EntradaPapelera) -> None:
    """Se llama dentro de la transacción que borra el registro (todo o nada)."""
    await cursor.execute(
        "INSERT INTO deleted_record (entity_type, entity_id, label, payload, "
        "deleted_by_account_id, deleted_by_name) VALUES (%s, %s, %s, %s, %s, %s)",
        (
            entrada.tipo,
            entrada.entidad_id,
            entrada.descripcion,
            json.dumps(entrada.datos, ensure_ascii=False),
            entrada.eliminado_por_id,
            entrada.eliminado_por,
        ),
    )


class PapeleraRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def listar(
        self, tipo: TipoRegistro | None, *, limit: int, offset: int
    ) -> tuple[list[RegistroEliminado], int]:
        clause, params = (" WHERE entity_type = %s", [tipo]) if tipo else ("", [])
        async with self._db.connection() as conn, conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                f"{_SELECT}{clause} ORDER BY deleted_record_id DESC LIMIT %s OFFSET %s",
                (*params, limit, offset),
            )
            rows = await cursor.fetchall()
            await cursor.execute(f"SELECT COUNT(*) AS total FROM deleted_record{clause}", params)
            total = (await cursor.fetchone())["total"]
        return [_registro(row) for row in rows], int(total)

    async def obtener(self, record_id: int) -> tuple[RegistroEliminado, dict[str, Any]] | None:
        async with self._db.connection() as conn, conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "SELECT deleted_record_id, entity_type, entity_id, label, deleted_at, "
                "deleted_by_name, payload FROM deleted_record WHERE deleted_record_id = %s",
                (record_id,),
            )
            row = await cursor.fetchone()
        if row is None:
            return None
        return _registro(row), json.loads(row["payload"])

    async def eliminar(self, record_id: int) -> bool:
        async with self._db.transaction() as conn, conn.cursor() as cursor:
            await cursor.execute(
                "DELETE FROM deleted_record WHERE deleted_record_id = %s", (record_id,)
            )
            return cursor.rowcount > 0


def _registro(row: dict[str, Any]) -> RegistroEliminado:
    return RegistroEliminado(
        id=row["deleted_record_id"],
        tipo=row["entity_type"],
        entidad_id=row["entity_id"],
        descripcion=row["label"],
        eliminado_en=en_utc(row["deleted_at"]),
        eliminado_por=row["deleted_by_name"],
    )
