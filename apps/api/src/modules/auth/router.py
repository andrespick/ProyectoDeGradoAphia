from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from modules.auth.dependencies import get_auth_service, get_current_principal
from modules.auth.schemas import CambioClaveRequest, LoginRequest, LoginResponse, Principal
from modules.auth.service import AuthService
from modules.configuracion.dependencies import get_configuracion_repository
from modules.configuracion.schemas import PoliticaPublica
from modules.configuracion.service import ConfiguracionRepositoryPort

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    datos: LoginRequest, service: Annotated[AuthService, Depends(get_auth_service)]
) -> LoginResponse:
    return await service.login(datos)


@router.get("/me", response_model=Principal)
async def me(principal: Annotated[Principal, Depends(get_current_principal)]) -> Principal:
    return principal


@router.post("/cambiar-clave", response_model=LoginResponse)
async def cambiar_clave(
    datos: CambioClaveRequest,
    principal: Annotated[Principal, Depends(get_current_principal)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> LoginResponse:
    return await service.cambiar_clave(principal, datos)


# Pública: la pantalla de inicio de sesión muestra los intentos y el tiempo de bloqueo vigentes.
@router.get("/politica", response_model=PoliticaPublica)
async def politica(
    repository: Annotated[ConfiguracionRepositoryPort, Depends(get_configuracion_repository)],
) -> PoliticaPublica:
    return PoliticaPublica(**(await repository.obtener_politica()).model_dump())
