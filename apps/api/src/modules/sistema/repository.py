from __future__ import annotations

import time
from typing import Any

import aiomysql

from db.connection import Database
from modules.auth.repository import en_utc
from modules.sistema.schemas import (
    ConteoRegistros,
    Diagnostico,
    EstadoBaseDatos,
    EstadoMigraciones,
    Respaldo,
)

_RESPALDO = (
    "SELECT backup_run_id, trigger_type, status, requested_at, started_at, finished_at, "
    "file_name, size_bytes, remote_copy, error_message FROM backup_run"
)
_CONTEOS = (
    "SELECT (SELECT COUNT(*) FROM person) AS personas, "
    "(SELECT COUNT(*) FROM property) AS inmuebles, "
    "(SELECT COUNT(*) FROM property_agreement) AS contratos, "
    "(SELECT COUNT(*) FROM user_account) AS usuarios, "
    "(SELECT COUNT(*) FROM audit_event) AS eventos_auditoria, "
    "(SELECT COUNT(*) FROM deleted_record) AS en_papelera"
)
_PENDIENTE = " WHERE status IN ('SOLICITADO', 'EN_CURSO') ORDER BY backup_run_id LIMIT 1"


class SistemaRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def diagnostico(self) -> Diagnostico:
        async with self._db.connection() as conn, conn.cursor(aiomysql.DictCursor) as cursor:
            inicio = time.perf_counter()
            await cursor.execute("SELECT VERSION() AS version")
            version = (await cursor.fetchone())["version"]
            latencia = round((time.perf_counter() - inicio) * 1000, 1)
            await cursor.execute(
                "SELECT COALESCE(SUM(data_length + index_length), 0) AS tamano "
                "FROM information_schema.tables WHERE table_schema = DATABASE()"
            )
            tamano = int((await cursor.fetchone())["tamano"])
            await cursor.execute(
                "SELECT COUNT(*) AS aplicadas, MAX(version) AS ultima, MAX(aplicada_en) AS fecha "
                "FROM schema_migrations"
            )
            migraciones = await cursor.fetchone()
            await cursor.execute(_CONTEOS)
            conteos = {clave: int(valor) for clave, valor in (await cursor.fetchone()).items()}
            await cursor.execute(
                f"{_RESPALDO} WHERE status = 'OK' ORDER BY backup_run_id DESC LIMIT 1"
            )
            ultimo = await cursor.fetchone()
            await cursor.execute(f"{_RESPALDO}{_PENDIENTE}")
            pendiente = await cursor.fetchone()
        return Diagnostico(
            base_de_datos=EstadoBaseDatos(
                disponible=True, latencia_ms=latencia, version=version, tamano_bytes=tamano
            ),
            migraciones=EstadoMigraciones(
                aplicadas=int(migraciones["aplicadas"]),
                ultima=migraciones["ultima"],
                aplicada_en=en_utc(migraciones["fecha"]),
            ),
            registros=ConteoRegistros(**conteos),
            ultimo_exitoso=None if ultimo is None else _respaldo(ultimo),
            pendiente=None if pendiente is None else _respaldo(pendiente),
        )

    async def listar_respaldos(self, *, limit: int, offset: int) -> tuple[list[Respaldo], int]:
        async with self._db.connection() as conn, conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                f"{_RESPALDO} ORDER BY backup_run_id DESC LIMIT %s OFFSET %s", (limit, offset)
            )
            rows = await cursor.fetchall()
            await cursor.execute("SELECT COUNT(*) AS total FROM backup_run")
            total = (await cursor.fetchone())["total"]
        return [_respaldo(row) for row in rows], int(total)

    async def solicitar_respaldo(self) -> Respaldo | None:
        """Anota una solicitud manual; ``None`` si ya hay una pendiente o en curso."""
        async with self._db.transaction() as conn, conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(f"{_RESPALDO}{_PENDIENTE} FOR UPDATE")
            if await cursor.fetchone() is not None:
                return None
            await cursor.execute(
                "INSERT INTO backup_run (trigger_type, status) VALUES ('MANUAL', 'SOLICITADO')"
            )
            await cursor.execute(f"{_RESPALDO} WHERE backup_run_id = %s", (cursor.lastrowid,))
            return _respaldo(await cursor.fetchone())


def _respaldo(row: dict[str, Any]) -> Respaldo:
    return Respaldo(
        id=row["backup_run_id"],
        origen=row["trigger_type"].lower(),
        estado=row["status"].lower(),
        solicitado_en=en_utc(row["requested_at"]),
        iniciado_en=en_utc(row["started_at"]),
        terminado_en=en_utc(row["finished_at"]),
        archivo=row["file_name"],
        tamano_bytes=row["size_bytes"],
        copia_externa=None if row["remote_copy"] is None else bool(row["remote_copy"]),
        error=row["error_message"],
    )
