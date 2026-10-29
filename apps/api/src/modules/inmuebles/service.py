from __future__ import annotations

from typing import Any, Protocol

from core.errors import ConflictError, NotFoundError
from modules.auth.schemas import Principal
from modules.inmuebles.schemas import Inmueble, InmuebleCreate, InmuebleFiltros, InmueblesPage
from modules.papelera.schemas import EntradaPapelera, entrada


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

    async def eliminar(self, property_id: int, papelera: EntradaPapelera) -> bool: ...


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

    async def eliminar(self, property_id: int, actor: Principal) -> None:
        inmueble = await self.obtener(property_id)
        contratos = await self._repository.contar_contratos(property_id)
        if contratos:
            raise InmuebleConContratosError(contratos)
        descripcion = ", ".join(filter(None, [inmueble.direccion, inmueble.ciudad]))
        papelera = entrada("inmueble", property_id, descripcion, _instantanea(inmueble), actor)
        if not await self._repository.eliminar(property_id, papelera):
            raise InmuebleNoEncontradoError()


def _instantanea(inmueble: Inmueble) -> dict[str, Any]:
    """Datos con la forma de ``InmuebleCreate`` para restaurarlo desde la papelera."""
    datos = inmueble.model_dump(
        mode="json", include={"direccion", "ciudad", "matricula", "canon", "estado"}
    )
    datos["servicios"] = [s.model_dump(mode="json", exclude={"id"}) for s in inmueble.servicios]
    datos["propietarios_ids"] = [p.id for p in inmueble.propietarios]
    return datos
