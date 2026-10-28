from __future__ import annotations

import aiomysql
import pymysql

from db.connection import Database
from db.sql import ER_DUP_ENTRY, mysql_error_code
from modules.clientes.schemas import Cliente
from modules.clientes.service import CorreoDuplicadoError


class ClientesRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def listar(self, *, limit: int, offset: int) -> tuple[list[Cliente], int]:
        async with self._db.connection() as conn, conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "SELECT id, nombre, correo, creado_en, actualizado_en FROM clientes "
                "ORDER BY id DESC LIMIT %s OFFSET %s",
                (limit, offset),
            )
            rows = await cursor.fetchall()
            await cursor.execute("SELECT COUNT(*) AS total FROM clientes")
            total_row = await cursor.fetchone()
        return [Cliente(**row) for row in rows], int(total_row["total"])

    async def crear(self, *, nombre: str, correo: str) -> Cliente:
        try:
            async with (
                self._db.transaction() as conn,
                conn.cursor(aiomysql.DictCursor) as cursor,
            ):
                await cursor.execute(
                    "INSERT INTO clientes (nombre, correo) VALUES (%s, %s)", (nombre, correo)
                )
                await cursor.execute(
                    "SELECT id, nombre, correo, creado_en, actualizado_en FROM clientes "
                    "WHERE id = %s",
                    (cursor.lastrowid,),
                )
                row = await cursor.fetchone()
        except pymysql.err.IntegrityError as exc:
            if mysql_error_code(exc) == ER_DUP_ENTRY:
                raise CorreoDuplicadoError() from exc
            raise
        return Cliente(**row)
