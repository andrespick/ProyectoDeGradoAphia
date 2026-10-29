from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from core.errors import AppError
from db.connection import Database
from db.dependencies import get_database
from modules.auth.dependencies import Auditar, require_roles
from modules.auth.schemas import GESTION_SISTEMA, TODOS
from modules.catalogos.repository import (
    CatalogosAdminRepository,
    CatalogosAdminRepositoryPort,
    CatalogosRepository,
    CatalogosRepositoryPort,
)
from modules.catalogos.schemas import (
    CatalogoAdministrable,
    Catalogos,
    ItemCatalogo,
    ItemCatalogoCreate,
    ItemCatalogoUpdate,
)

router = APIRouter(
    prefix="/api/v1/catalogos",
    tags=["catalogos"],
    dependencies=[Depends(require_roles(*TODOS))],
)
SoloAdmin = [Depends(require_roles(*GESTION_SISTEMA))]

# Catálogos con código (el resto son de nombre libre: ciudades, bancos, proveedores).
CON_CODIGO = {"tipos-identificacion", "tipos-contrato", "tipos-cuenta-bancaria", "tipos-servicio"}


class CodigoRequeridoError(AppError):
    status_code = 422
    code = "codigo_requerido"
    default_message = "Indique el código del nuevo valor."
    details = [  # noqa: RUF012 - constante de clase
        {"campo": "codigo", "ubicacion": "body", "mensaje": default_message, "tipo": code}
    ]


def get_catalogos_repository(
    db: Annotated[Database, Depends(get_database)],
) -> CatalogosRepositoryPort:
    return CatalogosRepository(db)


def get_catalogos_admin_repository(
    db: Annotated[Database, Depends(get_database)],
) -> CatalogosAdminRepositoryPort:
    return CatalogosAdminRepository(db)


Admin = Annotated[CatalogosAdminRepositoryPort, Depends(get_catalogos_admin_repository)]


@router.get("", response_model=Catalogos)
async def obtener_catalogos(
    repository: Annotated[CatalogosRepositoryPort, Depends(get_catalogos_repository)],
) -> Catalogos:
    return await repository.obtener()


@router.get("/{catalogo}", response_model=list[ItemCatalogo], dependencies=SoloAdmin)
async def listar_items(catalogo: CatalogoAdministrable, repository: Admin) -> list[ItemCatalogo]:
    return await repository.listar(catalogo)


@router.post(
    "/{catalogo}",
    response_model=ItemCatalogo,
    status_code=status.HTTP_201_CREATED,
    dependencies=SoloAdmin,
)
async def crear_item(
    catalogo: CatalogoAdministrable, datos: ItemCatalogoCreate, repository: Admin, auditar: Auditar
) -> ItemCatalogo:
    if catalogo in CON_CODIGO and not datos.codigo:
        raise CodigoRequeridoError()
    item = await repository.crear(catalogo, datos)
    await auditar.registrar("crear", "catalogo", item.id, f"{catalogo}: {item.nombre}")
    return item


@router.put("/{catalogo}/{id}", response_model=ItemCatalogo, dependencies=SoloAdmin)
async def renombrar_item(
    catalogo: CatalogoAdministrable,
    id: int,
    datos: ItemCatalogoUpdate,
    repository: Admin,
    auditar: Auditar,
) -> ItemCatalogo:
    item = await repository.renombrar(catalogo, id, datos.nombre)
    await auditar.registrar("actualizar", "catalogo", id, f"{catalogo}: {item.nombre}")
    return item


@router.delete("/{catalogo}/{id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=SoloAdmin)
async def eliminar_item(
    catalogo: CatalogoAdministrable, id: int, repository: Admin, auditar: Auditar
) -> Response:
    await repository.eliminar(catalogo, id)
    await auditar.registrar("eliminar", "catalogo", id, catalogo)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
