from __future__ import annotations

import logging
import math
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Protocol

from core.errors import AppError, AuthenticationRequiredError
from core.logging import get_logger, log_event
from modules.auth.passwords import DUMMY_HASH, verify_password
from modules.auth.repository import CuentaLogin
from modules.auth.schemas import LoginRequest, LoginResponse, Principal
from modules.auth.tokens import TOKEN_TTL_SECONDS, TokenPayload, issue_token

logger = get_logger("auth")

MAX_INTENTOS = 3
MINUTOS_BLOQUEO = 15


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

    async def register_failed_attempt(
        self, account_id: int, *, max_attempts: int, lock_minutes: int, now: datetime
    ) -> tuple[int, datetime | None]: ...

    async def reset_attempts(self, account_id: int) -> None: ...


class AuthService:
    def __init__(
        self,
        repository: AuthRepositoryPort,
        secret: str,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._repository = repository
        self._secret = secret
        self._now = now

    async def login(self, datos: LoginRequest) -> LoginResponse:
        now = self._now()
        cuenta = await self._repository.find_for_login(datos.usuario)
        if cuenta is None or not cuenta.is_active:
            verify_password(datos.clave, DUMMY_HASH)  # mismo coste que una cuenta real
            log_event(logger, logging.WARNING, "login_failed", motivo="cuenta_no_disponible")
            raise CredencialesInvalidasError()
        if cuenta.locked_until and cuenta.locked_until > now:
            log_event(logger, logging.WARNING, "login_blocked", account_id=cuenta.account_id)
            restante = math.ceil((cuenta.locked_until - now).total_seconds() / 60)
            raise CuentaBloqueadaError(max(restante, 1))
        if not verify_password(datos.clave, cuenta.hashed_password):
            intentos, bloqueada_hasta = await self._repository.register_failed_attempt(
                cuenta.account_id,
                max_attempts=MAX_INTENTOS,
                lock_minutes=MINUTOS_BLOQUEO,
                now=now,
            )
            log_event(
                logger,
                logging.WARNING,
                "login_failed",
                account_id=cuenta.account_id,
                intentos=intentos,
            )
            if bloqueada_hasta is not None:
                # Aviso al administrador: queda en los logs y visible en la pantalla de Usuarios.
                log_event(
                    logger,
                    logging.WARNING,
                    "cuenta_bloqueada",
                    account_id=cuenta.account_id,
                    bloqueada_hasta=bloqueada_hasta.isoformat(),
                )
                raise CuentaBloqueadaError(MINUTOS_BLOQUEO)
            raise CredencialesInvalidasError()

        await self._repository.reset_attempts(cuenta.account_id)
        principal = Principal(
            sujeto=str(cuenta.account_id), nombre=cuenta.nombre, roles=cuenta.roles, modo="database"
        )
        exp = int(now.timestamp()) + TOKEN_TTL_SECONDS
        token = issue_token(
            self._secret,
            TokenPayload(
                sub=principal.sujeto,
                nombre=principal.nombre,
                roles=[role.value for role in principal.roles],
                exp=exp,
            ),
        )
        log_event(logger, logging.INFO, "login_ok", account_id=cuenta.account_id)
        return LoginResponse(
            token=token, expira_en=datetime.fromtimestamp(exp, UTC), principal=principal
        )
