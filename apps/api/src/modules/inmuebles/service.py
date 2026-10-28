from __future__ import annotations

from typing import Protocol

from core.errors import ConflictError, NotFoundError
from modules.inmuebles.schemas import Inmueble, InmuebleCreate, InmuebleFiltros, InmueblesPage


class InmuebleNoEncontradoError(NotFoundError):
    code = "inmueble_no_encontrado"
    default_message = "El inmueble no existe."


class InmuebleConContratosError(ConflictError):
    code = "inmueble_con_contratos"

    def __init__(self, contratos: int) -> None:
        super().__init__(
            f"No se puede eliminar el inmueble: tiene {contratos} contrato(s). "
            "Elimine primero los contratos."
        )


class InmueblesRepositoryPort(Protocol):
    async def listar(
        self, filtros: InmuebleFiltros, *, limit: int, offset: int
    ) -> tuple[list[Inmueble], int]: ...

    async def obtener(self, property_id: int) -> Inmueble | None: ...

    async def crear(self, datos: InmuebleCreate) -> Inmueble: ...

    async def actualizar(self, property_id: int, datos: InmuebleCreate) -> Inmueble | None: ...

    async def contar_contratos(self, property_id: int) -> int: ...

    async def eliminar(self, property_id: int) -> bool: ...


class InmueblesService:
    def __init__(self, repository: InmueblesRepositoryPort) -> None:
        self._repository = repository

    async def listar(self, filtros: InmuebleFiltros, *, limit: int, offset: int) -> InmueblesPage:
        items, total = await self._repository.listar(filtros, limit=limit, offset=offset)
        return InmueblesPage(items=items, total=total, limit=limit, offset=offset)

    async def obtener(self, property_id: int) -> Inmueble:
        inmueble = await self._repository.obtener(property_id)
        if inmueble is None:
            raise InmuebleNoEncontradoError()
        return inmueble

    async def crear(self, datos: InmuebleCreate) -> Inmueble:
        return await self._repository.crear(datos)

    async def actualizar(self, property_id: int, datos: InmuebleCreate) -> Inmueble:
        inmueble = await self._repository.actualizar(property_id, datos)
        if inmueble is None:
            raise InmuebleNoEncontradoError()
        return inmueble

    async def eliminar(self, property_id: int) -> None:
        contratos = await self._repository.contar_contratos(property_id)
        if contratos:
            raise InmuebleConContratosError(contratos)
        if not await self._repository.eliminar(property_id):
            raise InmuebleNoEncontradoError()
