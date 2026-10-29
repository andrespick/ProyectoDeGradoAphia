from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from db.connection import Database
from db.dependencies import get_database
from modules.auth.dependencies import Auditar, get_current_principal, require_roles
from modules.auth.schemas import ELIMINACION, LECTURA, Principal
from modules.inmuebles.repository import InmueblesRepository
from modules.inmuebles.schemas import (
    Inmueble,
    InmuebleCreate,
    InmuebleFiltros,
    InmueblesPage,
    InmuebleUpdate,
)
from modules.inmuebles.service import InmueblesRepositoryPort, InmueblesService

router = APIRouter(
    prefix="/api/v1/inmuebles",
    tags=["inmuebles"],
    dependencies=[Depends(require_roles(*LECTURA))],
)


def get_inmuebles_repository(
    db: Annotated[Database, Depends(get_database)],
) -> InmueblesRepositoryPort:
    return InmueblesRepository(db)


def get_inmuebles_service(
    repository: Annotated[InmueblesRepositoryPort, Depends(get_inmuebles_repository)],
) -> InmueblesService:
    return InmueblesService(repository)


Service = Annotated[InmueblesService, Depends(get_inmuebles_service)]


@router.get("", response_model=InmueblesPage)
async def listar_inmuebles(
    service: Service,
    estado: Annotated[str | None, Query(max_length=30)] = None,
    ciudad: Annotated[str | None, Query(max_length=100)] = None,
    propietario_id: Annotated[int | None, Query(ge=1)] = None,
    q: Annotated[str | None, Query(max_length=100)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0, le=100_000)] = 0,
) -> InmueblesPage:
    filtros = InmuebleFiltros(estado=estado, ciudad=ciudad, propietario_id=propietario_id, q=q)
    return await service.listar(filtros, limit=limit, offset=offset)


@router.get("/{id}", response_model=Inmueble)
async def obtener_inmueble(id: int, service: Service) -> Inmueble:
    return await service.obtener(id)


@router.post("", response_model=Inmueble, status_code=status.HTTP_201_CREATED)
async def crear_inmueble(datos: InmuebleCreate, service: Service, auditar: Auditar) -> Inmueble:
    inmueble = await service.crear(datos)
    await auditar.registrar("crear", "inmueble", inmueble.id)
    return inmueble


@router.put("/{id}", response_model=Inmueble)
async def actualizar_inmueble(
    id: int, datos: InmuebleUpdate, service: Service, auditar: Auditar
) -> Inmueble:
    inmueble = await service.actualizar(id, datos)
    await auditar.registrar("actualizar", "inmueble", id)
    return inmueble


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(*ELIMINACION))],
)
async def eliminar_inmueble(
    id: int,
    service: Service,
    principal: Annotated[Principal, Depends(get_current_principal)],
    auditar: Auditar,
) -> Response:
    await service.eliminar(id, principal)
    await auditar.registrar("eliminar", "inmueble", id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
