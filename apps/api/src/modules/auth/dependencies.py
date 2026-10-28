from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, Request

from core.errors import AuthenticationRequiredError, PermissionDeniedError
from core.runtime import get_settings
from db.connection import Database
from db.dependencies import get_database
from modules.auth.repository import AuthRepository
from modules.auth.schemas import Principal, Role
from modules.auth.service import AuthRepositoryPort, AuthService
from modules.auth.tokens import verify_token

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
    if settings.auth_mode == "database" and settings.auth_secret:
        principal = _principal_from_bearer(
            settings.auth_secret, request.headers.get("authorization")
        )
        if principal is not None:
            return principal
        raise AuthenticationRequiredError("Inicie sesión para continuar.")
    raise AuthenticationRequiredError("La autenticación no está habilitada en este entorno.")


def _principal_from_bearer(secret: str, header: str | None) -> Principal | None:
    scheme, _, token = (header or "").partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    payload = verify_token(secret, token.strip())
    if payload is None:
        return None
    try:
        roles = [Role(role) for role in payload.roles]
    except ValueError:
        return None
    if not roles:
        return None
    return Principal(sujeto=payload.sub, nombre=payload.nombre, roles=roles, modo="database")


def require_roles(*allowed: Role) -> Callable[..., Awaitable[Principal]]:
    async def dependency(
        principal: Annotated[Principal, Depends(get_current_principal)],
    ) -> Principal:
        if not set(principal.roles) & set(allowed):
            raise PermissionDeniedError()
        return principal

    return dependency


def get_auth_repository(db: Annotated[Database, Depends(get_database)]) -> AuthRepositoryPort:
    return AuthRepository(db)


def get_auth_service(
    repository: Annotated[AuthRepositoryPort, Depends(get_auth_repository)], request: Request
) -> AuthService:
    settings = get_settings(request)
    if settings.auth_mode != "database" or not settings.auth_secret:
        raise AuthenticationRequiredError("El inicio de sesión no está habilitado en este entorno.")
    return AuthService(repository, settings.auth_secret)
