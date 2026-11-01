from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from modules.auth.dependencies import (
    Auditar,
    get_auth_repository,
    get_auth_service,
    get_current_principal,
)
from modules.auth.schemas import CambioClaveRequest, LoginRequest, LoginResponse, Principal
from modules.auth.service import AuthRepositoryPort, AuthService
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


# Invalida el token en el servidor (no solo en el navegador): cierra todas las sesiones de
# la cuenta, incluida la de otra pestaña o dispositivo con «Recordarme».
@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    principal: Annotated[Principal, Depends(get_current_principal)],
    repository: Annotated[AuthRepositoryPort, Depends(get_auth_repository)],
    auditar: Auditar,
) -> Response:
    if principal.modo == "database":
        account_id = int(principal.sujeto)
        await repository.cerrar_sesiones(account_id)
        await auditar.registrar("cierre_sesion", "usuario", account_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Pública: la pantalla de inicio de sesión muestra los intentos y el tiempo de bloqueo vigentes.
@router.get("/politica", response_model=PoliticaPublica)
async def politica(
    repository: Annotated[ConfiguracionRepositoryPort, Depends(get_configuracion_repository)],
) -> PoliticaPublica:
    return PoliticaPublica(**(await repository.obtener_politica()).model_dump())
