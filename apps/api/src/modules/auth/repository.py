from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import aiomysql

from db.connection import Database
from modules.auth.schemas import Role


@dataclass(frozen=True)
class CuentaLogin:
    account_id: int
    nombre: str
    hashed_password: str
    is_active: bool
    failed_login_attempts: int
    locked_until: datetime | None
    roles: list[Role]


_SELECT = (
    "SELECT ua.account_id, ua.hashed_password, ua.is_active, ua.failed_login_attempts, "
    "ua.locked_until, p.full_name, "
    "(SELECT GROUP_CONCAT(ar.code) FROM user_role ur JOIN app_role ar ON ar.role_id = ur.role_id "
    " WHERE ur.account_id = ua.account_id) AS roles "
    "FROM user_account ua JOIN person p ON p.person_id = ua.person_id "
    "WHERE ua.user_name = %s"
)


class AuthRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def find_for_login(self, user_name: str) -> CuentaLogin | None:
        # Comparación exacta (colación binaria): el nombre de usuario distingue mayúsculas.
        async with self._db.connection() as conn, conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(_SELECT, (user_name,))
            row = await cursor.fetchone()
        if row is None:
            return None
        return CuentaLogin(
            account_id=row["account_id"],
            nombre=row["full_name"] or user_name,
            hashed_password=row["hashed_password"],
            is_active=bool(row["is_active"]),
            failed_login_attempts=row["failed_login_attempts"],
            locked_until=en_utc(row["locked_until"]),
            roles=[Role.from_code(code) for code in (row["roles"] or "").split(",") if code],
        )

    async def register_failed_attempt(
        self, account_id: int, *, max_attempts: int, lock_minutes: int, now: datetime
    ) -> tuple[int, datetime | None]:
        """Suma un intento fallido y bloquea al llegar al máximo. Devuelve (intentos, bloqueo)."""
        async with (
            self._db.transaction() as conn,
            conn.cursor(aiomysql.DictCursor) as cursor,
        ):
            await cursor.execute(
                "SELECT failed_login_attempts, locked_until FROM user_account "
                "WHERE account_id = %s FOR UPDATE",
                (account_id,),
            )
            row = await cursor.fetchone()
            previous_lock = en_utc(row["locked_until"])
            # Un bloqueo ya vencido reinicia la cuenta de intentos.
            attempts = (
                1 if previous_lock and previous_lock <= now else row["failed_login_attempts"] + 1
            )
            locked_until = (
                now + timedelta(minutes=lock_minutes) if attempts >= max_attempts else None
            )
            await cursor.execute(
                "UPDATE user_account SET failed_login_attempts = %s, locked_until = %s "
                "WHERE account_id = %s",
                (attempts, sin_zona(locked_until), account_id),
            )
        return attempts, locked_until

    async def reset_attempts(self, account_id: int) -> None:
        async with self._db.transaction() as conn, conn.cursor() as cursor:
            await cursor.execute(
                "UPDATE user_account SET failed_login_attempts = 0, locked_until = NULL "
                "WHERE account_id = %s",
                (account_id,),
            )


def en_utc(value: datetime | None) -> datetime | None:
    """MySQL DATETIME no guarda zona horaria; la sesión usa UTC (+00:00)."""
    if value is None:
        return None
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


def sin_zona(value: datetime | None) -> datetime | None:
    return None if value is None else value.astimezone(UTC).replace(tzinfo=None)
