from __future__ import annotations

from typing import Protocol

from core.errors import ConflictError, NotFoundError
from modules.contratos.schemas import Contrato, ContratoCreate, ContratoFiltros, ContratosPage
from modules.inmuebles.service import InmuebleNoEncontradoError


class ContratoNoEncontradoError(NotFoundError):
    code = "contrato_no_encontrado"
    default_message = "El contrato no existe."


class InmuebleSinPropietarioError(ConflictError):
    code = "inmueble_sin_propietario"
    default_message = (
        "El inmueble no tiene propietarios registrados. Asócielos en Inmuebles o indíquelos "
        "en el contrato."
    )


class ContratoConDependenciasError(ConflictError):
    code = "contrato_con_dependencias"

    def __init__(self, financieros: int, archivos: int) -> None:
        partes = []
        if financieros:
            partes.append(f"{financieros} registro(s) financiero(s)")
        if archivos:
            partes.append(f"{archivos} archivo(s)")
        super().__init__(
            "No se puede modificar ni eliminar el contrato: tiene " + " y ".join(partes) + "."
        )


class ContratosRepositoryPort(Protocol):
    async def listar(
        self, filtros: ContratoFiltros, *, limit: int, offset: int
    ) -> tuple[list[Contrato], int]: ...

    async def obtener(self, agreement_id: int) -> Contrato | None: ...

    async def propietarios_del_inmueble(self, property_id: int) -> list[int] | None: ...

    async def crear(self, datos: ContratoCreate, propietarios_ids: list[int]) -> Contrato: ...

    async def actualizar(
        self, agreement_id: int, datos: ContratoCreate, propietarios_ids: list[int]
    ) -> Contrato | None: ...

    async def contar_dependencias(self, agreement_id: int) -> tuple[int, int]: ...

    async def eliminar(self, agreement_id: int) -> bool: ...


class ContratosService:
    def __init__(self, repository: ContratosRepositoryPort) -> None:
        self._repository = repository

    async def listar(self, filtros: ContratoFiltros, *, limit: int, offset: int) -> ContratosPage:
        items, total = await self._repository.listar(filtros, limit=limit, offset=offset)
        return ContratosPage(items=items, total=total, limit=limit, offset=offset)

    async def obtener(self, agreement_id: int) -> Contrato:
        contrato = await self._repository.obtener(agreement_id)
        if contrato is None:
            raise ContratoNoEncontradoError()
        return contrato

    async def crear(self, datos: ContratoCreate) -> Contrato:
        return await self._repository.crear(datos, await self._propietarios(datos))

    async def actualizar(self, agreement_id: int, datos: ContratoCreate) -> Contrato:
        await self._sin_dependencias(agreement_id)
        contrato = await self._repository.actualizar(
            agreement_id, datos, await self._propietarios(datos)
        )
        if contrato is None:
            raise ContratoNoEncontradoError()
        return contrato

    async def eliminar(self, agreement_id: int) -> None:
        await self._sin_dependencias(agreement_id)
        if not await self._repository.eliminar(agreement_id):
            raise ContratoNoEncontradoError()

    async def _propietarios(self, datos: ContratoCreate) -> list[int]:
        del_inmueble = await self._repository.propietarios_del_inmueble(datos.inmueble_id)
        if del_inmueble is None:
            raise InmuebleNoEncontradoError()
        propietarios = del_inmueble if datos.propietarios_ids is None else datos.propietarios_ids
        if not propietarios:
            raise InmuebleSinPropietarioError()
        return propietarios

    async def _sin_dependencias(self, agreement_id: int) -> None:
        financieros, archivos = await self._repository.contar_dependencias(agreement_id)
        if financieros or archivos:
            raise ContratoConDependenciasError(financieros, archivos)
