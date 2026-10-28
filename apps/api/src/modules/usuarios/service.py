from __future__ import annotations

import logging
from typing import Protocol

from core.errors import ConflictError, NotFoundError
from core.logging import get_logger, log_event
from modules.auth.passwords import hash_password
from modules.auth.schemas import Principal, Role
from modules.usuarios.repository import UsuarioDuplicadoError as _Duplicado
from modules.usuarios.schemas import (
    EstadoUsuario,
    Usuario,
    UsuarioCreate,
    UsuariosPage,
    UsuarioUpdate,
)

logger = get_logger("usuarios")


class UsuarioNoEncontradoError(NotFoundError):
    code = "usuario_no_encontrado"
    default_message = "El usuario no existe."


class UsuarioDuplicadoError(ConflictError):
    code = "usuario_duplicado"
    default_message = "Ya existe un usuario con ese nombre de usuario."


class UltimoAdministradorError(ConflictError):
    code = "ultimo_administrador"
    default_message = "No se puede dejar el sistema sin un Administrador de Sistemas activo."


class UsuarioActualError(ConflictError):
    code = "usuario_actual"
    default_message = "No puede eliminar ni desactivar su propia cuenta."


class UsuariosRepositoryPort(Protocol):
    async def listar(
        self,
        *,
        q: str | None,
        rol: Role | None,
        estado: EstadoUsuario | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Usuario], int]: ...

    async def obtener(self, account_id: int) -> Usuario | None: ...

    async def crear(self, datos: UsuarioCreate, hashed_password: str) -> Usuario: ...

    async def actualizar(
        self, account_id: int, datos: UsuarioUpdate, hashed_password: str | None
    ) -> Usuario | None: ...

    async def eliminar(self, account_id: int) -> bool: ...

    async def count_other_active_admins(self, account_id: int) -> int: ...

    async def unlock(self, account_id: int) -> Usuario | None: ...


class UsuariosService:
    def __init__(self, repository: UsuariosRepositoryPort) -> None:
        self._repository = repository

    async def listar(
        self,
        *,
        q: str | None,
        rol: Role | None,
        estado: EstadoUsuario | None,
        limit: int,
        offset: int,
    ) -> UsuariosPage:
        items, total = await self._repository.listar(
            q=q, rol=rol, estado=estado, limit=limit, offset=offset
        )
        return UsuariosPage(items=items, total=total, limit=limit, offset=offset)

    async def obtener(self, account_id: int) -> Usuario:
        usuario = await self._repository.obtener(account_id)
        if usuario is None:
            raise UsuarioNoEncontradoError()
        return usuario

    async def crear(self, datos: UsuarioCreate) -> Usuario:
        try:
            return await self._repository.crear(datos, hash_password(datos.clave))
        except _Duplicado as exc:
            raise UsuarioDuplicadoError() from exc

    async def actualizar(
        self, account_id: int, datos: UsuarioUpdate, principal: Principal
    ) -> Usuario:
        actual = await self.obtener(account_id)
        if str(account_id) == principal.sujeto and not datos.activo:
            raise UsuarioActualError()
        pierde_admin = datos.rol != Role.ADMIN_SISTEMAS or not datos.activo
        if actual.rol == Role.ADMIN_SISTEMAS and actual.activo and pierde_admin:
            await self._exigir_otro_admin(account_id)
        hashed = hash_password(datos.clave) if datos.clave else None
        usuario = await self._repository.actualizar(account_id, datos, hashed)
        if usuario is None:
            raise UsuarioNoEncontradoError()
        return usuario

    async def eliminar(self, account_id: int, principal: Principal) -> None:
        if str(account_id) == principal.sujeto:
            raise UsuarioActualError()
        actual = await self.obtener(account_id)
        if actual.rol == Role.ADMIN_SISTEMAS and actual.activo:
            await self._exigir_otro_admin(account_id)
        if not await self._repository.eliminar(account_id):
            raise UsuarioNoEncontradoError()

    async def desbloquear(self, account_id: int, principal: Principal) -> Usuario:
        usuario = await self._repository.unlock(account_id)
        if usuario is None:
            raise UsuarioNoEncontradoError()
        log_event(
            logger,
            logging.INFO,
            "usuario_desbloqueado",
            account_id=account_id,
            por=principal.sujeto,
        )
        return usuario

    async def _exigir_otro_admin(self, account_id: int) -> None:
        if await self._repository.count_other_active_admins(account_id) == 0:
            raise UltimoAdministradorError()
