from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, Request

from core.errors import AuthenticationRequiredError, PermissionDeniedError
from core.runtime import get_settings
from modules.auth.schemas import Principal, Role

DEVELOPMENT_PRINCIPAL = Principal(
    sujeto="desarrollo-local",
    nombre="Usuario de desarrollo",
    roles=[Role.ADMIN_SISTEMAS],
    modo="development",
)


async def get_current_principal(request: Request) -> Principal:
    settings = get_settings(request)
    # Doble verificación: Settings ya rechaza AUTH_MODE=development fuera de entornos locales.
    if settings.auth_mode == "development" and settings.is_local:
        return DEVELOPMENT_PRINCIPAL
    raise AuthenticationRequiredError(
        "La autenticación todavía no está implementada para este entorno."
    )


def require_roles(*allowed: Role) -> Callable[..., Awaitable[Principal]]:
    async def dependency(
        principal: Annotated[Principal, Depends(get_current_principal)],
    ) -> Principal:
        if not set(principal.roles) & set(allowed):
            raise PermissionDeniedError()
        return principal

    return dependency
