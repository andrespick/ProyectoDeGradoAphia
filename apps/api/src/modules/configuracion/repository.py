from __future__ import annotations

import aiomysql

from db.connection import Database
from modules.configuracion.schemas import Empresa, PoliticaSeguridad
from modules.inmuebles.repository import ciudad_id

_POLITICA = (
    "SELECT max_failed_attempts, lock_minutes, session_hours, min_password_length "
    "FROM security_policy WHERE security_policy_id = 1"
)
_EMPRESA = (
    "SELECT o.legal_name, o.tax_identifier, o.address, c.name AS ciudad, o.phone_number, "
    "o.email_address FROM organization_profile o LEFT JOIN city c ON c.city_id = o.city_id "
    "WHERE o.organization_profile_id = 1"
)


class ConfiguracionRepository:
    """Las filas únicas (id = 1) las crea la migración 0018; aquí solo se leen y actualizan."""

    def __init__(self, db: Database) -> None:
        self._db = db

    async def obtener_politica(self) -> PoliticaSeguridad:
        async with self._db.connection() as conn, conn.cursor(aiomysql.DictCursor) as cursor:
            return await _politica(cursor)

    async def guardar_politica(self, politica: PoliticaSeguridad) -> PoliticaSeguridad:
        async with self._db.transaction() as conn, conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "UPDATE security_policy SET max_failed_attempts = %s, lock_minutes = %s, "
                "session_hours = %s, min_password_length = %s WHERE security_policy_id = 1",
                (
                    politica.max_intentos,
                    politica.minutos_bloqueo,
                    politica.horas_sesion,
                    politica.largo_minimo_clave,
                ),
            )
            return await _politica(cursor)

    async def obtener_empresa(self) -> Empresa:
        async with self._db.connection() as conn, conn.cursor(aiomysql.DictCursor) as cursor:
            return await _empresa(cursor)

    async def guardar_empresa(self, empresa: Empresa) -> Empresa:
        async with self._db.transaction() as conn, conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "UPDATE organization_profile SET legal_name = %s, tax_identifier = %s, "
                "address = %s, city_id = %s, phone_number = %s, email_address = %s "
                "WHERE organization_profile_id = 1",
                (
                    empresa.nombre,
                    empresa.nit,
                    empresa.direccion,
                    await ciudad_id(cursor, empresa.ciudad),
                    empresa.telefono,
                    empresa.correo,
                ),
            )
            return await _empresa(cursor)


async def _politica(cursor: aiomysql.DictCursor) -> PoliticaSeguridad:
    await cursor.execute(_POLITICA)
    row = await cursor.fetchone()
    return PoliticaSeguridad(
        max_intentos=row["max_failed_attempts"],
        minutos_bloqueo=row["lock_minutes"],
        horas_sesion=row["session_hours"],
        largo_minimo_clave=row["min_password_length"],
    )


async def _empresa(cursor: aiomysql.DictCursor) -> Empresa:
    await cursor.execute(_EMPRESA)
    row = await cursor.fetchone()
    return Empresa(
        nombre=row["legal_name"],
        nit=row["tax_identifier"],
        direccion=row["address"],
        ciudad=row["ciudad"],
        telefono=row["phone_number"],
        correo=row["email_address"],
    )
