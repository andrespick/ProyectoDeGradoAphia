from __future__ import annotations

from typing import Protocol

from core.errors import ConflictError
from modules.clientes.schemas import Cliente, ClienteCreate, ClientesPage


class CorreoDuplicadoError(ConflictError):
    code = "correo_duplicado"
    default_message = "Ya existe un cliente registrado con ese correo electrónico."


class ClientesRepositoryPort(Protocol):
    async def listar(self, *, limit: int, offset: int) -> tuple[list[Cliente], int]: ...

    async def crear(self, *, nombre: str, correo: str) -> Cliente: ...


class ClientesService:
    def __init__(self, repository: ClientesRepositoryPort) -> None:
        self._repository = repository

    async def listar(self, *, limit: int, offset: int) -> ClientesPage:
        items, total = await self._repository.listar(limit=limit, offset=offset)
        return ClientesPage(items=items, total=total, limit=limit, offset=offset)

    async def crear(self, datos: ClienteCreate) -> Cliente:
        return await self._repository.crear(nombre=datos.nombre, correo=datos.correo)
