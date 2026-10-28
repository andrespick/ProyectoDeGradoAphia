from __future__ import annotations

from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response, status

from db.connection import Database
from db.dependencies import get_database
from modules.auth.dependencies import require_roles
from modules.auth.schemas import ELIMINACION, LECTURA
from modules.contratos.repository import ContratosRepository
from modules.contratos.schemas import (
    Contrato,
    ContratoCreate,
    ContratoFiltros,
    ContratoListado,
    ContratosPage,
    ContratoUpdate,
)
from modules.contratos.service import ContratosRepositoryPort, ContratosService

router = APIRouter(
    prefix="/api/v1/contratos",
    tags=["contratos"],
    dependencies=[Depends(require_roles(*LECTURA))],
)


def get_contratos_repository(
    db: Annotated[Database, Depends(get_database)],
) -> ContratosRepositoryPort:
    return ContratosRepository(db)


def get_contratos_service(
    repository: Annotated[ContratosRepositoryPort, Depends(get_contratos_repository)],
) -> ContratosService:
    return ContratosService(repository)


Service = Annotated[ContratosService, Depends(get_contratos_service)]


@router.get("", response_model=ContratosPage)
async def listar_contratos(
    service: Service,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    inmueble_id: Annotated[int | None, Query(ge=1)] = None,
    propietario_id: Annotated[int | None, Query(ge=1)] = None,
    inquilino_id: Annotated[int | None, Query(ge=1)] = None,
    tipo: Annotated[str | None, Query(max_length=30)] = None,
    estado: Literal["vigente", "por_vencer", "finalizado", "programado"] | None = None,
    q: Annotated[str | None, Query(max_length=100)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0, le=100_000)] = 0,
) -> ContratosPage:
    filtros = ContratoFiltros(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        inmueble_id=inmueble_id,
        propietario_id=propietario_id,
        inquilino_id=inquilino_id,
        tipo=tipo,
        estado=estado,
        q=q,
    )
    pagina = await service.listar(filtros, limit=limit, offset=offset)
    # El listado omite el texto completo y las condiciones (pueden pesar cientos de KB).
    return ContratosPage(
        items=[ContratoListado.model_validate(c, from_attributes=True) for c in pagina.items],
        total=pagina.total,
        limit=limit,
        offset=offset,
    )


@router.get("/{id}", response_model=Contrato)
async def obtener_contrato(id: int, service: Service) -> Contrato:
    return await service.obtener(id)


@router.post("", response_model=Contrato, status_code=status.HTTP_201_CREATED)
async def crear_contrato(datos: ContratoCreate, service: Service) -> Contrato:
    return await service.crear(datos)


@router.put("/{id}", response_model=Contrato)
async def actualizar_contrato(id: int, datos: ContratoUpdate, service: Service) -> Contrato:
    return await service.actualizar(id, datos)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(*ELIMINACION))],
)
async def eliminar_contrato(id: int, service: Service) -> Response:
    await service.eliminar(id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
