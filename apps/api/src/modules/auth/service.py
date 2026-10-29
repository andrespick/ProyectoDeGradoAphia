from __future__ import annotations

import logging
import math
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Protocol

from core.errors import AppError, AuthenticationRequiredError
from core.logging import get_logger, log_event
from modules.auditoria.service import Auditor
from modules.auth.passwords import DUMMY_HASH, hash_password, verify_password
from modules.auth.repository import CuentaLogin, EstadoSesion
from modules.auth.schemas import CambioClaveRequest, LoginRequest, LoginResponse, Principal
from modules.auth.tokens import TokenPayload, issue_token
from modules.configuracion.schemas import PoliticaSeguridad
from modules.configuracion.service import ClaveInseguraError, exigir_clave_segura

logger = get_logger("auth")


class CredencialesInvalidasError(AuthenticationRequiredError):
    code = "credenciales_invalidas"
    default_message = "Usuario o contraseña incorrectos."


class CuentaBloqueadaError(AppError):
    status_code = 423
    code = "cuenta_bloqueada"

    def __init__(self, minutos: int) -> None:
        super().__init__(
            f"La cuenta está bloqueada temporalmente. Intente de nuevo en {minutos} minuto(s) "
            "o pida al Administrador de Sistemas que la desbloquee."
        )


class AuthRepositoryPort(Protocol):
    async def find_for_login(self, user_name: str) -> CuentaLogin | None: ...

    async def find_by_id(self, account_id: int) -> CuentaLogin | None: ...

    async def register_failed_attempt(
        self, account_id: int, *, max_attempts: int, lock_minutes: int, now: datetime
    ) -> tuple[int, datetime | None]: ...

    async def reset_attempts(self, account_id: int) -> None: ...

    async def estado_sesion(self, account_id: int) -> EstadoSesion | None: ...

    async def cambiar_clave(self, account_id: int, hashed_password: str) -> int: ...


class AuthService:
    def __init__(
        self,
        repository: AuthRepositoryPort,
        secret: str,
        politica: PoliticaSeguridad,
        auditor: Auditor,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._repository = repository
        self._secret = secret
        self._politica = politica
        self._auditor = auditor
        self._now = now

    async def login(self, datos: LoginRequest) -> LoginResponse:
        now = self._now()
        cuenta = await self._repository.find_for_login(datos.usuario)
        if cuenta is None or not cuenta.is_active:
            verify_password(datos.clave, DUMMY_HASH)  # mismo coste que una cuenta real
            # Solo en los logs: auditarlo dejaría a cualquiera escribir filas sin límite
            # (no hay bloqueo para una cuenta inexistente o inactiva).
            log_event(logger, logging.WARNING, "login_failed", motivo="cuenta_no_disponible")
            raise CredencialesInvalidasError()
        if cuenta.locked_until and cuenta.locked_until > now:
            # Tampoco se audita: el bloqueo ya quedó registrado como «cuenta_bloqueada».
            log_event(logger, logging.WARNING, "login_blocked", account_id=cuenta.account_id)
            restante = math.ceil((cuenta.locked_until - now).total_seconds() / 60)
            raise CuentaBloqueadaError(max(restante, 1))
        if not verify_password(datos.clave, cuenta.hashed_password):
            intentos, bloqueada_hasta = await self._repository.register_failed_attempt(
                cuenta.account_id,
                max_attempts=self._politica.max_intentos,
                lock_minutes=self._politica.minutos_bloqueo,
                now=now,
            )
            log_event(
                logger,
                logging.WARNING,
                "login_failed",
                account_id=cuenta.account_id,
                intentos=intentos,
            )
            await self._auditar(cuenta, "inicio_sesion_fallido", f"intento {intentos}")
            if bloqueada_hasta is not None:
                # Aviso al administrador: queda en los logs, en la auditoría y en Usuarios.
                log_event(
                    logger,
                    logging.WARNING,
                    "cuenta_bloqueada",
                    account_id=cuenta.account_id,
                    bloqueada_hasta=bloqueada_hasta.isoformat(),
                )
                await self._auditar(
                    cuenta, "cuenta_bloqueada", f"{self._politica.minutos_bloqueo} minutos"
                )
                raise CuentaBloqueadaError(self._politica.minutos_bloqueo)
            raise CredencialesInvalidasError()

        await self._repository.reset_attempts(cuenta.account_id)
        log_event(logger, logging.INFO, "login_ok", account_id=cuenta.account_id)
        await self._auditar(cuenta, "inicio_sesion")
        return self._sesion(cuenta, cuenta.session_version, cuenta.debe_cambiar_clave)

    async def cambiar_clave(self, principal: Principal, datos: CambioClaveRequest) -> LoginResponse:
        cuenta = (
            await self._repository.find_by_id(int(principal.sujeto))
            if principal.sujeto.isdigit()
            else None
        )
        if cuenta is None:
            raise AuthenticationRequiredError("Inicie sesión para continuar.")
        if not verify_password(datos.clave_actual, cuenta.hashed_password):
            raise ClaveInseguraError("La clave actual no es correcta.", "clave_actual")
        if datos.clave_nueva == datos.clave_actual:
            raise ClaveInseguraError(
                "La clave nueva debe ser distinta de la actual.", "clave_nueva"
            )
        exigir_clave_segura(datos.clave_nueva, self._politica, "clave_nueva")
        version = await self._repository.cambiar_clave(
            cuenta.account_id, hash_password(datos.clave_nueva)
        )
        await self._auditar(cuenta, "cambio_clave")
        # Las demás sesiones quedan cerradas; esta continúa con un token nuevo.
        return self._sesion(cuenta, version, debe_cambiar_clave=False)

    async def _auditar(self, cuenta: CuentaLogin, accion: str, detalle: str | None = None) -> None:
        await self._auditor.registrar(
            accion,
            "usuario",
            cuenta.account_id,
            detalle,
            actor_id=cuenta.account_id,
            actor_nombre=cuenta.nombre,
        )

    def _sesion(self, cuenta: CuentaLogin, version: int, debe_cambiar_clave: bool) -> LoginResponse:
        principal = Principal(
            sujeto=str(cuenta.account_id),
            nombre=cuenta.nombre,
            roles=cuenta.roles,
            modo="database",
            debe_cambiar_clave=debe_cambiar_clave,
        )
        exp = int(self._now().timestamp()) + self._politica.horas_sesion * 3600
        token = issue_token(
            self._secret,
            TokenPayload(
                sub=principal.sujeto,
                nombre=principal.nombre,
                roles=[role.value for role in principal.roles],
                exp=exp,
                ver=version,
            ),
        )
        return LoginResponse(
            token=token, expira_en=datetime.fromtimestamp(exp, UTC), principal=principal
        )
