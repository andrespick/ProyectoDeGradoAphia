from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, Request

from core.errors import AuthenticationRequiredError, PermissionDeniedError, request_id_of
from core.runtime import get_settings
from db.connection import Database
from db.dependencies import get_database
from modules.auditoria.dependencies import get_auditoria_repository
from modules.auditoria.service import Auditor, AuditoriaRepositoryPort
from modules.auth.repository import AuthRepository
from modules.auth.schemas import Principal, Role
from modules.auth.service import AuthRepositoryPort, AuthService
from modules.auth.tokens import TokenPayload, verify_token
from modules.configuracion.dependencies import get_configuracion_repository
from modules.configuracion.service import ConfiguracionRepositoryPort

DEVELOPMENT_PRINCIPAL = Principal(
    sujeto="desarrollo-local",
    nombre="Usuario de desarrollo",
    # Ambos roles: en desarrollo local se necesita ver los usuarios y los módulos de negocio.
    roles=[Role.ADMIN_SISTEMAS, Role.ADMINISTRATIVO],
    modo="development",
)


class CambioDeClaveRequeridoError(PermissionDeniedError):
    code = "cambio_de_clave_requerido"
    default_message = "Debe cambiar su contraseña antes de continuar."


def get_auth_repository(db: Annotated[Database, Depends(get_database)]) -> AuthRepositoryPort:
    return AuthRepository(db)


async def get_current_principal(
    request: Request, repository: Annotated[AuthRepositoryPort, Depends(get_auth_repository)]
) -> Principal:
    settings = get_settings(request)
    # Doble verificación: Settings ya rechaza AUTH_MODE=development fuera de entornos locales.
    if settings.auth_mode == "development" and settings.is_local:
        return DEVELOPMENT_PRINCIPAL
    if settings.auth_mode == "database" and settings.auth_secret:
        payload = _payload_from_bearer(settings.auth_secret, request.headers.get("authorization"))
        if payload is None:
            raise AuthenticationRequiredError("Inicie sesión para continuar.")
        # Una consulta por solicitud: la desactivación, el cambio de rol y el cierre de sesiones
        # surten efecto de inmediato (incrementan session_version).
        estado = await repository.estado_sesion(int(payload.sub))
        if estado is None or not estado.activa or estado.version != payload.ver:
            raise AuthenticationRequiredError("Su sesión se cerró. Inicie sesión de nuevo.")
        return Principal(
            sujeto=payload.sub,
            nombre=payload.nombre,
            roles=[Role(role) for role in payload.roles],
            modo="database",
            debe_cambiar_clave=estado.debe_cambiar_clave,
        )
    raise AuthenticationRequiredError("La autenticación no está habilitada en este entorno.")


def _payload_from_bearer(secret: str, header: str | None) -> TokenPayload | None:
    scheme, _, token = (header or "").partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    payload = verify_token(secret, token.strip())
    if payload is None or not payload.sub.isdigit() or not payload.roles:
        return None
    if not set(payload.roles) <= {role.value for role in Role}:
        return None
    return payload


def require_roles(*allowed: Role) -> Callable[..., Awaitable[Principal]]:
    async def dependency(
        principal: Annotated[Principal, Depends(get_current_principal)],
    ) -> Principal:
        if principal.debe_cambiar_clave:
            raise CambioDeClaveRequeridoError()
        if not set(principal.roles) & set(allowed):
            raise PermissionDeniedError()
        return principal

    return dependency


def get_auditor(
    request: Request,
    repository: Annotated[AuditoriaRepositoryPort, Depends(get_auditoria_repository)],
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> Auditor:
    return Auditor(repository, principal, request_id_of(request))


# Los routers registran cada escritura: ``await auditar.registrar("crear", "inmueble", id)``.
Auditar = Annotated[Auditor, Depends(get_auditor)]


async def get_auth_service(
    request: Request,
    repository: Annotated[AuthRepositoryPort, Depends(get_auth_repository)],
    configuracion: Annotated[ConfiguracionRepositoryPort, Depends(get_configuracion_repository)],
    auditoria: Annotated[AuditoriaRepositoryPort, Depends(get_auditoria_repository)],
) -> AuthService:
    settings = get_settings(request)
    if settings.auth_mode != "database" or not settings.auth_secret:
        raise AuthenticationRequiredError("El inicio de sesión no está habilitado en este entorno.")
    return AuthService(
        repository,
        settings.auth_secret,
        await configuracion.obtener_politica(),
        Auditor(auditoria, request_id=request_id_of(request)),
    )
