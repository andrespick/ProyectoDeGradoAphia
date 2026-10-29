from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from db.connection import Database
from db.dependencies import get_database
from modules.auth.dependencies import Auditar, get_current_principal, require_roles
from modules.auth.schemas import GESTION_SISTEMA, Principal, Role
from modules.configuracion.dependencies import get_configuracion_repository
from modules.configuracion.service import ConfiguracionRepositoryPort
from modules.usuarios.repository import UsuariosRepository
from modules.usuarios.schemas import (
    ClaveTemporal,
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
    dependencies=[Depends(require_roles(*GESTION_SISTEMA))],
)


def get_usuarios_repository(
    db: Annotated[Database, Depends(get_database)],
) -> UsuariosRepositoryPort:
    return UsuariosRepository(db)


def get_usuarios_service(
    repository: Annotated[UsuariosRepositoryPort, Depends(get_usuarios_repository)],
    configuracion: Annotated[ConfiguracionRepositoryPort, Depends(get_configuracion_repository)],
) -> UsuariosService:
    return UsuariosService(repository, configuracion)


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
async def crear_usuario(datos: UsuarioCreate, service: Service, auditar: Auditar) -> Usuario:
    usuario = await service.crear(datos)
    await auditar.registrar("crear", "usuario", usuario.id, f"rol {usuario.rol.value}")
    return usuario


@router.put("/{id}", response_model=Usuario)
async def actualizar_usuario(
    id: int, datos: UsuarioUpdate, service: Service, principal: Actor, auditar: Auditar
) -> Usuario:
    usuario = await service.actualizar(id, datos, principal)
    await auditar.registrar(
        "actualizar", "usuario", id, "con cambio de clave" if datos.clave else None
    )
    return usuario


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_usuario(
    id: int, service: Service, principal: Actor, auditar: Auditar
) -> Response:
    await service.eliminar(id, principal)
    await auditar.registrar("eliminar", "usuario", id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{id}/desbloquear", response_model=Usuario)
async def desbloquear_usuario(
    id: int, service: Service, principal: Actor, auditar: Auditar
) -> Usuario:
    usuario = await service.desbloquear(id, principal)
    await auditar.registrar("desbloquear", "usuario", id)
    return usuario


@router.post("/{id}/restablecer-clave", response_model=ClaveTemporal)
async def restablecer_clave(
    id: int, service: Service, principal: Actor, auditar: Auditar
) -> ClaveTemporal:
    clave = await service.restablecer_clave(id, principal)
    await auditar.registrar("restablecer_clave", "usuario", id)
    return clave


@router.post("/{id}/cerrar-sesiones", status_code=status.HTTP_204_NO_CONTENT)
async def cerrar_sesiones(
    id: int, service: Service, principal: Actor, auditar: Auditar
) -> Response:
    await service.cerrar_sesiones(id, principal)
    await auditar.registrar("cerrar_sesiones", "usuario", id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
