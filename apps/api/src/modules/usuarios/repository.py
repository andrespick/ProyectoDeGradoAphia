# ruff: noqa: S608 - el SQL se arma solo con fragmentos fijos; los valores van parametrizados
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import aiomysql
import pymysql

from core.errors import CatalogoInvalidoError, IdentificacionDuplicadaError
from db.connection import Database
from db.sql import ER_DUP_ENTRY, like_pattern, mysql_error_code
from modules.auth.repository import en_utc
from modules.auth.schemas import Role
from modules.usuarios.schemas import EstadoUsuario, Usuario, UsuarioCreate, UsuarioUpdate

_SELECT = (
    "SELECT ua.account_id, ua.user_name, ua.login_email, ua.is_active, ua.created_at, "
    "ua.failed_login_attempts, ua.locked_until, p.person_id, p.full_name, "
    "dt.code AS tipo_identificacion, d.document_identifier, "
    "(SELECT GROUP_CONCAT(ar.code) FROM user_role ur JOIN app_role ar ON ar.role_id = ur.role_id "
    " WHERE ur.account_id = ua.account_id) AS roles "
    "FROM user_account ua "
    "JOIN person p ON p.person_id = ua.person_id "
    "LEFT JOIN person_document d ON d.person_document_id = "
    " (SELECT MIN(person_document_id) FROM person_document WHERE person_id = p.person_id) "
    "LEFT JOIN document_type dt ON dt.document_type_id = d.document_type_id"
)
_ESTADOS = {
    "activo": (
        "ua.is_active = 1 AND (ua.locked_until IS NULL OR ua.locked_until <= UTC_TIMESTAMP(6))"
    ),
    "inactivo": "ua.is_active = 0",
    "bloqueado": "ua.locked_until > UTC_TIMESTAMP(6)",
}
_TIPO_DOCUMENTO = (
    "SELECT document_type_id FROM document_type WHERE issuer_scope = 'CO' AND code = %s"
)


class UsuariosRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def listar(
        self,
        *,
        q: str | None,
        rol: Role | None,
        estado: EstadoUsuario | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Usuario], int]:
        where: list[str] = []
        params: list[Any] = []
        if q:
            where.append("(ua.user_name LIKE %s OR p.full_name COLLATE utf8mb4_0900_ai_ci LIKE %s)")
            params += [like_pattern(q), like_pattern(q)]
        if rol:
            where.append(
                "EXISTS (SELECT 1 FROM user_role ur JOIN app_role ar ON ar.role_id = ur.role_id "
                "WHERE ur.account_id = ua.account_id AND ar.code = %s)"
            )
            params.append(rol.code)
        if estado:
            where.append(_ESTADOS[estado])
        clause = f" WHERE {' AND '.join(where)}" if where else ""
        async with self._db.connection() as conn, conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                f"{_SELECT}{clause} ORDER BY ua.user_name LIMIT %s OFFSET %s",
                (*params, limit, offset),
            )
            rows = await cursor.fetchall()
            await cursor.execute(
                f"SELECT COUNT(*) AS total FROM user_account ua JOIN person p "
                f"ON p.person_id = ua.person_id{clause}",
                params,
            )
            total = (await cursor.fetchone())["total"]
        return [_usuario(row) for row in rows], int(total)

    async def obtener(self, account_id: int) -> Usuario | None:
        async with self._db.connection() as conn, conn.cursor(aiomysql.DictCursor) as cursor:
            return await _fetch(cursor, account_id)

    async def crear(self, datos: UsuarioCreate, hashed_password: str) -> Usuario:
        try:
            async with (
                self._db.transaction() as conn,
                conn.cursor(aiomysql.DictCursor) as cursor,
            ):
                person_id = await _buscar_persona(
                    cursor, datos.tipo_identificacion, datos.identificacion
                )
                if person_id is None:
                    person_id = await _crear_persona(cursor, datos)
                await cursor.execute(
                    "INSERT INTO user_account (person_id, user_name, login_email, hashed_password, "
                    "is_active) VALUES (%s, %s, %s, %s, %s)",
                    (person_id, datos.usuario, datos.correo, hashed_password, datos.activo),
                )
                account_id = cursor.lastrowid
                await _asignar_rol(cursor, account_id, datos.rol)
                usuario = await _fetch(cursor, account_id)
        except pymysql.err.IntegrityError as exc:
            if mysql_error_code(exc) == ER_DUP_ENTRY:
                raise UsuarioDuplicadoError() from exc
            raise
        assert usuario is not None  # noqa: S101 - recién insertado en la misma transacción
        return usuario

    async def actualizar(
        self, account_id: int, datos: UsuarioUpdate, hashed_password: str | None
    ) -> Usuario | None:
        try:
            async with (
                self._db.transaction() as conn,
                conn.cursor(aiomysql.DictCursor) as cursor,
            ):
                await cursor.execute(
                    "SELECT person_id FROM user_account WHERE account_id = %s FOR UPDATE",
                    (account_id,),
                )
                row = await cursor.fetchone()
                if row is None:
                    return None
                person_id = row["person_id"]
                await cursor.execute(
                    "UPDATE person SET full_name = %s WHERE person_id = %s",
                    (datos.nombre, person_id),
                )
                await _guardar_documento(
                    cursor, person_id, datos.tipo_identificacion, datos.identificacion
                )
                campos = "login_email = %s, is_active = %s"
                params: list[Any] = [datos.correo, datos.activo]
                if hashed_password is not None:
                    campos += ", hashed_password = %s"
                    params.append(hashed_password)
                await cursor.execute(
                    f"UPDATE user_account SET {campos} WHERE account_id = %s",
                    (*params, account_id),
                )
                await cursor.execute("DELETE FROM user_role WHERE account_id = %s", (account_id,))
                await _asignar_rol(cursor, account_id, datos.rol)
                return await _fetch(cursor, account_id)
        except pymysql.err.IntegrityError as exc:
            if mysql_error_code(exc) == ER_DUP_ENTRY:
                raise IdentificacionDuplicadaError() from exc
            raise

    async def eliminar(self, account_id: int) -> bool:
        async with self._db.transaction() as conn, conn.cursor() as cursor:
            await cursor.execute("DELETE FROM user_role WHERE account_id = %s", (account_id,))
            await cursor.execute("DELETE FROM user_account WHERE account_id = %s", (account_id,))
            return cursor.rowcount > 0

    async def count_other_active_admins(self, account_id: int) -> int:
        async with self._db.connection() as conn, conn.cursor() as cursor:
            await cursor.execute(
                "SELECT COUNT(*) FROM user_account ua "
                "JOIN user_role ur ON ur.account_id = ua.account_id "
                "JOIN app_role ar ON ar.role_id = ur.role_id "
                "WHERE ar.code = %s AND ua.is_active = 1 AND ua.account_id <> %s",
                (Role.ADMIN_SISTEMAS.code, account_id),
            )
            return int((await cursor.fetchone())[0])

    async def unlock(self, account_id: int) -> Usuario | None:
        async with (
            self._db.transaction() as conn,
            conn.cursor(aiomysql.DictCursor) as cursor,
        ):
            await cursor.execute(
                "UPDATE user_account SET failed_login_attempts = 0, locked_until = NULL "
                "WHERE account_id = %s",
                (account_id,),
            )
            return await _fetch(cursor, account_id)


class UsuarioDuplicadoError(Exception):
    """Marcador interno; el service lo traduce al error de dominio (evita import circular)."""


async def _fetch(cursor: aiomysql.DictCursor, account_id: int) -> Usuario | None:
    await cursor.execute(f"{_SELECT} WHERE ua.account_id = %s", (account_id,))
    row = await cursor.fetchone()
    return None if row is None else _usuario(row)


async def _buscar_persona(cursor: aiomysql.DictCursor, tipo: str, numero: str) -> int | None:
    await cursor.execute(
        "SELECT d.person_id FROM person_document d "
        "JOIN document_type dt ON dt.document_type_id = d.document_type_id "
        "WHERE dt.issuer_scope = 'CO' AND dt.code = %s AND d.document_identifier = %s",
        (tipo, numero),
    )
    row = await cursor.fetchone()
    return None if row is None else int(row["person_id"])


async def _crear_persona(cursor: aiomysql.DictCursor, datos: UsuarioCreate) -> int:
    await cursor.execute("INSERT INTO person (full_name) VALUES (%s)", (datos.nombre,))
    person_id = cursor.lastrowid
    await cursor.execute(
        "INSERT INTO person_document (person_id, document_type_id, document_identifier) "
        f"SELECT %s, document_type_id, %s FROM ({_TIPO_DOCUMENTO}) AS t",
        (person_id, datos.identificacion, datos.tipo_identificacion),
    )
    if cursor.rowcount == 0:
        raise CatalogoInvalidoError("tipo_identificacion")
    return int(person_id)


async def _guardar_documento(
    cursor: aiomysql.DictCursor, person_id: int, tipo: str, numero: str
) -> None:
    await cursor.execute(_TIPO_DOCUMENTO, (tipo,))
    row = await cursor.fetchone()
    if row is None:
        raise CatalogoInvalidoError("tipo_identificacion")
    await cursor.execute(
        "UPDATE person_document SET document_type_id = %s, document_identifier = %s "
        "WHERE person_document_id = (SELECT id FROM (SELECT MIN(person_document_id) AS id "
        "FROM person_document WHERE person_id = %s) AS x)",
        (row["document_type_id"], numero, person_id),
    )
    if cursor.rowcount == 0:
        await cursor.execute(
            "INSERT IGNORE INTO person_document (person_id, document_type_id, document_identifier) "
            "VALUES (%s, %s, %s)",
            (person_id, row["document_type_id"], numero),
        )


async def _asignar_rol(cursor: aiomysql.DictCursor, account_id: int, rol: Role) -> None:
    await cursor.execute(
        "INSERT INTO user_role (account_id, role_id) "
        "SELECT %s, role_id FROM app_role WHERE code = %s",
        (account_id, rol.code),
    )
    if cursor.rowcount == 0:
        raise CatalogoInvalidoError("rol")


def _usuario(row: dict[str, Any]) -> Usuario:
    bloqueada_hasta = en_utc(row["locked_until"])
    roles = [Role.from_code(code) for code in (row["roles"] or "").split(",") if code]
    return Usuario(
        id=row["account_id"],
        usuario=row["user_name"],
        nombre=row["full_name"] or row["user_name"],
        tipo_identificacion=row["tipo_identificacion"],
        identificacion=row["document_identifier"],
        correo=row["login_email"],
        rol=roles[0] if roles else Role.ASESOR,
        activo=bool(row["is_active"]),
        bloqueada=bloqueada_hasta is not None and bloqueada_hasta > datetime.now(UTC),
        bloqueada_hasta=bloqueada_hasta,
        intentos_fallidos=row["failed_login_attempts"],
        creado_en=en_utc(row["created_at"]),
    )
