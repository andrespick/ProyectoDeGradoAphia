from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from modules.auth.dependencies import get_auth_service, get_current_principal
from modules.auth.schemas import LoginRequest, LoginResponse, Principal
from modules.auth.service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    datos: LoginRequest, service: Annotated[AuthService, Depends(get_auth_service)]
) -> LoginResponse:
    return await service.login(datos)


@router.get("/me", response_model=Principal)
async def me(principal: Annotated[Principal, Depends(get_current_principal)]) -> Principal:
    return principal
