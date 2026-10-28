from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from modules.auth.dependencies import get_current_principal
from modules.auth.schemas import Principal

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.get("/me", response_model=Principal)
async def me(principal: Annotated[Principal, Depends(get_current_principal)]) -> Principal:
    return principal
