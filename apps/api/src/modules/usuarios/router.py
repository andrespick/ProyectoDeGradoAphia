from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from db.connection import Database
from db.dependencies import get_database
from modules.auth.dependencies import get_current_principal, require_roles
from modules.auth.schemas import GESTION_USUARIOS, Principal, Role
from modules.usuarios.repository import UsuariosRepository
from modules.usuarios.schemas import (
    EstadoUsuario,
    Usuario,
    UsuarioCreate,
    UsuariosPage,
    UsuarioUpdate,
)
from modules.usuarios.service import UsuariosRepositoryPort, UsuariosService

router = APIRouter(
    prefix="/api/v1/usuarios",
    tags=["usuarios"],
    dependencies=[Depends(require_roles(*GESTION_USUARIOS))],
)


def get_usuarios_repository(
    db: Annotated[Database, Depends(get_database)],
) -> UsuariosRepositoryPort:
    return UsuariosRepository(db)


def get_usuarios_service(
    repository: Annotated[UsuariosRepositoryPort, Depends(get_usuarios_repository)],
) -> UsuariosService:
    return UsuariosService(repository)


Service = Annotated[UsuariosService, Depends(get_usuarios_service)]
Actor = Annotated[Principal, Depends(get_current_principal)]


@router.get("", response_model=UsuariosPage)
async def listar_usuarios(
    service: Service,
    q: Annotated[str | None, Query(max_length=100)] = None,
    rol: Role | None = None,
    estado: EstadoUsuario | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0, le=100_000)] = 0,
) -> UsuariosPage:
    return await service.listar(q=q, rol=rol, estado=estado, limit=limit, offset=offset)


@router.get("/{id}", response_model=Usuario)
async def obtener_usuario(id: int, service: Service) -> Usuario:
    return await service.obtener(id)


@router.post("", response_model=Usuario, status_code=status.HTTP_201_CREATED)
async def crear_usuario(datos: UsuarioCreate, service: Service) -> Usuario:
    return await service.crear(datos)


@router.put("/{id}", response_model=Usuario)
async def actualizar_usuario(
    id: int, datos: UsuarioUpdate, service: Service, principal: Actor
) -> Usuario:
    return await service.actualizar(id, datos, principal)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_usuario(id: int, service: Service, principal: Actor) -> Response:
    await service.eliminar(id, principal)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{id}/desbloquear", response_model=Usuario)
async def desbloquear_usuario(id: int, service: Service, principal: Actor) -> Usuario:
    return await service.desbloquear(id, principal)
