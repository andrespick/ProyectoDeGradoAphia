from __future__ import annotations

from typing import Protocol

import aiomysql

from db.connection import Database
from modules.auth.schemas import Role
from modules.catalogos.schemas import PAPEL_POR_CODIGO, Catalogos, Ciudad, Opcion

_OPCIONES = {
    "tipos_identificacion": (
        "SELECT code, name FROM document_type WHERE issuer_scope = 'CO' ORDER BY name"
    ),
    "estados_ocupacion": "SELECT code, name FROM occupancy_state ORDER BY name",
    "tipos_contrato": "SELECT code, name FROM agreement_category ORDER BY name",
    "tipos_cuenta_bancaria": "SELECT code, name FROM bank_account_category ORDER BY name",
    "tipos_servicio": "SELECT code, name FROM utility_type ORDER BY name",
    "monedas": "SELECT currency_code AS code, name FROM currency ORDER BY name",
}


class CatalogosRepositoryPort(Protocol):
    async def obtener(self) -> Catalogos: ...


class CatalogosRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def obtener(self) -> Catalogos:
        async with self._db.connection() as conn, conn.cursor(aiomysql.DictCursor) as cursor:
            opciones = {clave: await _opciones(cursor, sql) for clave, sql in _OPCIONES.items()}
            papeles = await _por_codigo(cursor, "SELECT code, name FROM party_role")
            roles = await _por_codigo(cursor, "SELECT code, name FROM app_role")
            await cursor.execute("SELECT city_id, name FROM city ORDER BY name")
            ciudades = [Ciudad(id=r["city_id"], nombre=r["name"]) for r in await cursor.fetchall()]
            bancos = await _nombres(cursor, "SELECT name FROM financial_institution ORDER BY name")
            proveedores = await _nombres(cursor, "SELECT name FROM service_provider ORDER BY name")
        return Catalogos(
            **opciones,
            # Orden fijo (propietario, arrendatario, codeudor) y solo los papeles conocidos.
            papeles=[
                Opcion(codigo=papel, nombre=papeles[codigo])
                for codigo, papel in PAPEL_POR_CODIGO.items()
                if codigo in papeles
            ],
            roles=[
                Opcion(codigo=rol.value, nombre=roles[rol.code])
                for rol in Role
                if rol.code in roles
            ],
            ciudades=ciudades,
            bancos=bancos,
            proveedores_servicios=proveedores,
        )


async def _opciones(cursor: aiomysql.DictCursor, sql: str) -> list[Opcion]:
    await cursor.execute(sql)
    return [Opcion(codigo=row["code"], nombre=row["name"]) for row in await cursor.fetchall()]


async def _por_codigo(cursor: aiomysql.DictCursor, sql: str) -> dict[str, str]:
    await cursor.execute(sql)
    return {row["code"]: row["name"] for row in await cursor.fetchall()}


async def _nombres(cursor: aiomysql.DictCursor, sql: str) -> list[str]:
    await cursor.execute(sql)
    return [row["name"] for row in await cursor.fetchall()]
