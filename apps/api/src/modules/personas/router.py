from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from db.connection import Database
from db.dependencies import get_database
from modules.auth.dependencies import require_roles
from modules.auth.schemas import ELIMINACION, LECTURA
from modules.personas.repository import PersonasRepository
from modules.personas.schemas import (
    Papel,
    Persona,
    PersonaCreate,
    PersonaDetalle,
    PersonaFiltros,
    PersonasPage,
    PersonaUpdate,
)
from modules.personas.service import PersonasRepositoryPort, PersonasService


def get_personas_repository(
    db: Annotated[Database, Depends(get_database)],
) -> PersonasRepositoryPort:
    return PersonasRepository(db)


def get_personas_service(
    repository: Annotated[PersonasRepositoryPort, Depends(get_personas_repository)],
) -> PersonasService:
    return PersonasService(repository)


Service = Annotated[PersonasService, Depends(get_personas_service)]


def build_personas_router(prefix: str, tag: str, papel_fijo: Papel | None) -> APIRouter:
    """Router CRUD sobre personas. ``papel_fijo`` restringe la lista y se añade al crear."""
    router = APIRouter(prefix=prefix, tags=[tag], dependencies=[Depends(require_roles(*LECTURA))])

    @router.get("", response_model=PersonasPage)
    async def listar(
        service: Service,
        q: Annotated[str | None, Query(max_length=100)] = None,
        correo: Annotated[str | None, Query(max_length=254)] = None,
        contrato_id: Annotated[int | None, Query(ge=1)] = None,
        papel: Papel | None = None,
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
        offset: Annotated[int, Query(ge=0, le=100_000)] = 0,
    ) -> PersonasPage:
        filtros = PersonaFiltros(
            q=q,
            correo=correo,
            papel=papel_fijo or papel,
            contrato_id=contrato_id,
            solo_con_papel=papel_fijo is None,
        )
        return await service.listar(filtros, limit=limit, offset=offset)

    @router.get("/{id}", response_model=PersonaDetalle)
    async def obtener(id: int, service: Service) -> PersonaDetalle:
        return await service.obtener(id)

    @router.post("", response_model=Persona, status_code=status.HTTP_201_CREATED)
    async def crear(datos: PersonaCreate, service: Service) -> Persona:
        return await service.crear(datos, papel_fijo)

    @router.put("/{id}", response_model=Persona)
    async def actualizar(id: int, datos: PersonaUpdate, service: Service) -> Persona:
        return await service.actualizar(id, datos, papel_fijo)

    @router.delete(
        "/{id}",
        status_code=status.HTTP_204_NO_CONTENT,
        dependencies=[Depends(require_roles(*ELIMINACION))],
    )
    async def eliminar(id: int, service: Service) -> Response:
        await service.eliminar(id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return router


# Búsqueda exacta por identificación para los selectores (incluye personas sin papel).
router = APIRouter(
    prefix="/api/v1/personas",
    tags=["personas"],
    dependencies=[Depends(require_roles(*LECTURA))],
)


@router.get("/buscar", response_model=Persona)
async def buscar_persona(
    service: Service,
    tipo_identificacion: Annotated[str, Query(min_length=1, max_length=20)],
    identificacion: Annotated[str, Query(min_length=1, max_length=50)],
) -> Persona:
    return await service.buscar(tipo_identificacion, identificacion)
