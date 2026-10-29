from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Protocol

from core.errors import ConflictError, ServiceUnavailableError
from modules.sistema.schemas import (
    HORAS_RESPALDO_ATRASADO,
    Diagnostico,
    EstadoApi,
    EstadoBaseDatos,
    EstadoRespaldos,
    EstadoSistema,
    Respaldo,
    RespaldosPage,
)


class RespaldoEnCursoError(ConflictError):
    code = "respaldo_en_curso"
    default_message = "Ya hay un respaldo solicitado o en curso. Espere a que termine."


class SistemaRepositoryPort(Protocol):
    async def diagnostico(self) -> Diagnostico: ...

    async def listar_respaldos(self, *, limit: int, offset: int) -> tuple[list[Respaldo], int]: ...

    async def solicitar_respaldo(self) -> Respaldo | None: ...


class SistemaService:
    def __init__(
        self,
        repository: SistemaRepositoryPort,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._repository = repository
        self._now = now

    async def estado(self, api: EstadoApi) -> EstadoSistema:
        try:
            diagnostico = await self._repository.diagnostico()
        except ServiceUnavailableError:
            # El panel sigue respondiendo: justamente sirve para ver que la base no está.
            return EstadoSistema(api=api, base_de_datos=EstadoBaseDatos(disponible=False))
        ultimo = diagnostico.ultimo_exitoso
        limite = self._now() - timedelta(hours=HORAS_RESPALDO_ATRASADO)
        return EstadoSistema(
            api=api,
            base_de_datos=diagnostico.base_de_datos,
            migraciones=diagnostico.migraciones,
            registros=diagnostico.registros,
            respaldos=EstadoRespaldos(
                ultimo_exitoso=ultimo,
                pendiente=diagnostico.pendiente,
                atrasado=ultimo is None
                or ultimo.terminado_en is None
                or ultimo.terminado_en < limite,
            ),
        )

    async def respaldos(self, *, limit: int, offset: int) -> RespaldosPage:
        items, total = await self._repository.listar_respaldos(limit=limit, offset=offset)
        return RespaldosPage(items=items, total=total, limit=limit, offset=offset)

    async def solicitar_respaldo(self) -> Respaldo:
        respaldo = await self._repository.solicitar_respaldo()
        if respaldo is None:
            raise RespaldoEnCursoError()
        return respaldo
