from __future__ import annotations

import logging
from typing import Protocol

from core.errors import ServiceUnavailableError
from core.logging import get_logger, log_event
from modules.auditoria.schemas import AuditoriaFiltros, EventoAuditoria, NuevoEvento
from modules.auth.schemas import Principal

logger = get_logger("auditoria")


class AuditoriaRepositoryPort(Protocol):
    async def registrar(self, evento: NuevoEvento) -> None: ...

    async def listar(
        self, filtros: AuditoriaFiltros, *, limit: int, offset: int
    ) -> tuple[list[EventoAuditoria], int]: ...


def actor_id_de(principal: Principal) -> int | None:
    """El sujeto es el ``account_id``; el usuario ficticio de desarrollo no tiene cuenta."""
    return int(principal.sujeto) if principal.sujeto.isdigit() else None


class Auditor:
    def __init__(
        self,
        repository: AuditoriaRepositoryPort,
        actor: Principal | None = None,
        request_id: str | None = None,
    ) -> None:
        self._repository = repository
        self._actor_id = actor_id_de(actor) if actor else None
        self._actor_nombre = actor.nombre if actor else None
        self._request_id = request_id

    async def registrar(
        self,
        accion: str,
        entidad: str | None = None,
        entidad_id: int | None = None,
        detalle: str | None = None,
        *,
        actor_id: int | None = None,
        actor_nombre: str | None = None,
    ) -> None:
        """``actor_*`` sustituye al usuario autenticado (inicio de sesión, aún sin principal)."""
        evento = NuevoEvento(
            accion=accion,
            entidad=entidad,
            entidad_id=entidad_id,
            detalle=detalle,
            actor_id=actor_id if actor_id is not None else self._actor_id,
            actor_nombre=actor_nombre if actor_nombre is not None else self._actor_nombre,
            request_id=self._request_id,
        )
        try:
            await self._repository.registrar(evento)
        except ServiceUnavailableError:
            # La operación ya se confirmó: no se revierte por no poder auditarla.
            log_event(
                logger, logging.WARNING, "auditoria_no_registrada", accion=accion, entidad=entidad
            )
