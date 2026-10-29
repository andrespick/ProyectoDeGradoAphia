# ruff: noqa: S608 - el SQL se arma solo con fragmentos fijos; los valores van parametrizados
from __future__ import annotations

from datetime import timedelta
from typing import Any

import aiomysql

from core.fechas import inicio_del_dia_utc
from db.connection import Database
from db.sql import like_pattern
from modules.auditoria.schemas import AuditoriaFiltros, EventoAuditoria, NuevoEvento
from modules.auth.repository import en_utc

_SELECT = (
    "SELECT ae.audit_event_id, ae.occurred_at, ae.actor_account_id, ae.actor_name, "
    "ua.user_name, ae.action, ae.entity_type, ae.entity_id, ae.detail, ae.request_id "
    "FROM audit_event ae LEFT JOIN user_account ua ON ua.account_id = ae.actor_account_id"
)


class AuditoriaRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def registrar(self, evento: NuevoEvento) -> None:
        async with self._db.transaction() as conn, conn.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO audit_event (actor_account_id, actor_name, action, entity_type, "
                "entity_id, detail, request_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (
                    evento.actor_id,
                    evento.actor_nombre,
                    evento.accion,
                    evento.entidad,
                    evento.entidad_id,
                    evento.detalle[:255] if evento.detalle else None,
                    evento.request_id,
                ),
            )

    async def listar(
        self, filtros: AuditoriaFiltros, *, limit: int, offset: int
    ) -> tuple[list[EventoAuditoria], int]:
        where: list[str] = []
        params: list[Any] = []
        if filtros.accion:
            where.append("ae.action = %s")
            params.append(filtros.accion)
        if filtros.entidad:
            where.append("ae.entity_type = %s")
            params.append(filtros.entidad)
        if filtros.entidad_id is not None:
            where.append("ae.entity_id = %s")
            params.append(filtros.entidad_id)
        if filtros.q:
            where.append(
                "(ae.actor_name COLLATE utf8mb4_0900_ai_ci LIKE %s OR ua.user_name LIKE %s)"
            )
            params += [like_pattern(filtros.q), like_pattern(filtros.q)]
        # Las fechas del filtro son días de Colombia; occurred_at está en UTC.
        if filtros.desde:
            where.append("ae.occurred_at >= %s")
            params.append(inicio_del_dia_utc(filtros.desde))
        if filtros.hasta:
            where.append("ae.occurred_at < %s")
            params.append(inicio_del_dia_utc(filtros.hasta + timedelta(days=1)))
        clause = f" WHERE {' AND '.join(where)}" if where else ""
        async with self._db.connection() as conn, conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                f"{_SELECT}{clause} ORDER BY ae.audit_event_id DESC LIMIT %s OFFSET %s",
                (*params, limit, offset),
            )
            rows = await cursor.fetchall()
            await cursor.execute(
                "SELECT COUNT(*) AS total FROM audit_event ae "
                f"LEFT JOIN user_account ua ON ua.account_id = ae.actor_account_id{clause}",
                params,
            )
            total = (await cursor.fetchone())["total"]
        return [_evento(row) for row in rows], int(total)


def _evento(row: dict[str, Any]) -> EventoAuditoria:
    return EventoAuditoria(
        id=row["audit_event_id"],
        fecha=en_utc(row["occurred_at"]),
        actor_id=row["actor_account_id"],
        actor_nombre=row["actor_name"],
        actor_usuario=row["user_name"],
        accion=row["action"],
        entidad=row["entity_type"],
        entidad_id=row["entity_id"],
        detalle=row["detail"],
        request_id=row["request_id"],
    )
