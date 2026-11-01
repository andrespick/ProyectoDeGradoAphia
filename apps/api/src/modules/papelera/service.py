from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from typing import Any, Protocol

from pydantic import ValidationError

from core.errors import AppError, ConflictError, NotFoundError
from modules.contratos.schemas import ContratoCreate
from modules.contratos.service import ContratosService
from modules.inmuebles.schemas import InmuebleCreate
from modules.inmuebles.service import InmueblesService
from modules.papelera.schemas import (
    PapeleraPage,
    RegistroEliminado,
    Restaurado,
    TipoRegistro,
)
from modules.personas.schemas import PersonaCreate
from modules.personas.service import PersonasService


class RegistroEliminadoNoEncontradoError(NotFoundError):
    code = "registro_eliminado_no_encontrado"
    default_message = "El registro no está en la papelera."


class RestauracionImposibleError(ConflictError):
    code = "restauracion_imposible"


class PapeleraRepositoryPort(Protocol):
    async def listar(
        self, tipo: TipoRegistro | None, *, limit: int, offset: int
    ) -> tuple[list[RegistroEliminado], int]: ...

    def restaurando(
        self, record_id: int
    ) -> AbstractAsyncContextManager[tuple[RegistroEliminado, dict[str, Any]] | None]: ...

    async def eliminar(self, record_id: int) -> bool: ...


class PapeleraService:
    def __init__(
        self,
        repository: PapeleraRepositoryPort,
        personas: PersonasService,
        inmuebles: InmueblesService,
        contratos: ContratosService,
    ) -> None:
        self._repository = repository
        self._personas = personas
        self._inmuebles = inmuebles
        self._contratos = contratos

    async def listar(self, tipo: TipoRegistro | None, *, limit: int, offset: int) -> PapeleraPage:
        items, total = await self._repository.listar(tipo, limit=limit, offset=offset)
        return PapeleraPage(items=items, total=total, limit=limit, offset=offset)

    async def restaurar(self, record_id: int) -> tuple[RegistroEliminado, Restaurado]:
        # Un doble clic o dos administradores a la vez no crean el registro dos veces.
        async with self._repository.restaurando(record_id) as encontrado:
            if encontrado is None:
                raise RegistroEliminadoNoEncontradoError()
            registro, datos = encontrado
            try:
                nuevo_id = await self._crear(registro.tipo, datos)
            except ValidationError as exc:
                raise RestauracionImposibleError(
                    "No se puede restaurar: los datos guardados ya no cumplen las validaciones."
                ) from exc
            except AppError as exc:
                if exc.status_code >= 500:
                    raise
                # Ej.: la identificación ya se registró de nuevo o el inmueble ya no existe.
                raise RestauracionImposibleError(f"No se puede restaurar: {exc.message}") from exc
        return registro, Restaurado(tipo=registro.tipo, id=nuevo_id)

    async def eliminar(self, record_id: int) -> None:
        if not await self._repository.eliminar(record_id):
            raise RegistroEliminadoNoEncontradoError()

    async def _crear(self, tipo: TipoRegistro, datos: dict[str, Any]) -> int:
        if tipo == "persona":
            return (await self._personas.crear(PersonaCreate.model_validate(datos), None)).id
        if tipo == "inmueble":
            return (await self._inmuebles.crear(InmuebleCreate.model_validate(datos))).id
        return (await self._contratos.crear(ContratoCreate.model_validate(datos))).id
