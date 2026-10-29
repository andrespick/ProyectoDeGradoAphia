from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from modules.auth.dependencies import Auditar, require_roles
from modules.auth.schemas import GESTION_SISTEMA, TODOS
from modules.configuracion.dependencies import get_configuracion_repository
from modules.configuracion.schemas import Empresa, PoliticaSeguridad
from modules.configuracion.service import ConfiguracionRepositoryPort

router = APIRouter(prefix="/api/v1/configuracion", tags=["configuracion"])

Repository = Annotated[ConfiguracionRepositoryPort, Depends(get_configuracion_repository)]
SoloAdmin = [Depends(require_roles(*GESTION_SISTEMA))]


@router.get("/seguridad", response_model=PoliticaSeguridad, dependencies=SoloAdmin)
async def obtener_politica(repository: Repository) -> PoliticaSeguridad:
    return await repository.obtener_politica()


@router.put("/seguridad", response_model=PoliticaSeguridad, dependencies=SoloAdmin)
async def guardar_politica(
    datos: PoliticaSeguridad, repository: Repository, auditar: Auditar
) -> PoliticaSeguridad:
    politica = await repository.guardar_politica(datos)
    await auditar.registrar(
        "actualizar",
        "politica_seguridad",
        detalle=(
            f"{politica.max_intentos} intentos, {politica.minutos_bloqueo} min, "
            f"{politica.horas_sesion} h, clave de {politica.largo_minimo_clave}"
        ),
    )
    return politica


# Todos los roles: la impresión de contratos y el pie de página usan estos datos.
@router.get("/empresa", response_model=Empresa, dependencies=[Depends(require_roles(*TODOS))])
async def obtener_empresa(repository: Repository) -> Empresa:
    return await repository.obtener_empresa()


@router.put("/empresa", response_model=Empresa, dependencies=SoloAdmin)
async def guardar_empresa(datos: Empresa, repository: Repository, auditar: Auditar) -> Empresa:
    empresa = await repository.guardar_empresa(datos)
    await auditar.registrar("actualizar", "empresa")
    return empresa
