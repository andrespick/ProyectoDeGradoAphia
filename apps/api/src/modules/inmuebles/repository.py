# ruff: noqa: S608 - el SQL se arma solo con fragmentos fijos; los valores van parametrizados
from __future__ import annotations

from collections import defaultdict
from typing import Any

import aiomysql
import pymysql

from core.errors import CatalogoInvalidoError, RegistroReferenciadoError
from db.connection import Database
from db.sql import ER_NO_REFERENCED_ROW, ER_ROW_IS_REFERENCED, like_pattern, mysql_error_code
from modules.inmuebles.schemas import (
    Inmueble,
    InmuebleCreate,
    InmuebleFiltros,
    ServicioPublico,
    ServicioPublicoCreate,
)
from modules.personas.repository import agregar_papeles
from modules.personas.schemas import PersonaResumen
from modules.personas.service import PersonaNoEncontradaError

_SELECT = (
    "SELECT p.property_id, p.address, c.name AS ciudad, p.registration_identifier, "
    "p.rental_value, p.currency_code, os.code AS estado, "
    "(SELECT COUNT(*) FROM property_agreement a WHERE a.property_id = p.property_id) "
    " AS total_contratos "
    "FROM property p "
    "LEFT JOIN city c ON c.city_id = p.city_id "
    "LEFT JOIN occupancy_state os ON os.occupancy_state_id = p.occupancy_state_id"
)
# Resumen de persona con una fila hija por campo (misma regla que modules.personas).
PROPIETARIOS_SQL = (
    "SELECT po.property_id, pe.person_id, pe.full_name, dt.code AS tipo_identificacion, "
    "d.document_identifier, ph.phone_number, e.email_address "
    "FROM property_owner po JOIN person pe ON pe.person_id = po.person_id "
    "LEFT JOIN person_document d ON d.person_document_id = "
    " (SELECT MIN(person_document_id) FROM person_document WHERE person_id = pe.person_id) "
    "LEFT JOIN document_type dt ON dt.document_type_id = d.document_type_id "
    "LEFT JOIN person_phone ph ON ph.phone_id = "
    " (SELECT MIN(phone_id) FROM person_phone WHERE person_id = pe.person_id) "
    "LEFT JOIN person_email e ON e.email_id = "
    " (SELECT MIN(email_id) FROM person_email WHERE person_id = pe.person_id) "
    "WHERE po.property_id IN ({marcadores}) ORDER BY pe.full_name"
)
_SERVICIOS = (
    "SELECT pu.property_utility_id, pu.property_id, ut.code AS tipo, sp.name AS proveedor, "
    "pu.contract_identifier FROM property_utility pu "
    "LEFT JOIN utility_type ut ON ut.utility_type_id = pu.utility_type_id "
    "LEFT JOIN service_provider sp ON sp.provider_id = pu.provider_id "
    "WHERE pu.property_id IN ({marcadores}) ORDER BY pu.property_utility_id"
)


class InmueblesRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def listar(
        self, filtros: InmuebleFiltros, *, limit: int, offset: int
    ) -> tuple[list[Inmueble], int]:
        where, params = _where(filtros)
        async with self._db.connection() as conn, conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                f"{_SELECT}{where} ORDER BY p.property_id DESC LIMIT %s OFFSET %s",
                (*params, limit, offset),
            )
            rows = await cursor.fetchall()
            await cursor.execute(
                "SELECT COUNT(*) AS total FROM property p "
                "LEFT JOIN city c ON c.city_id = p.city_id "
                "LEFT JOIN occupancy_state os ON os.occupancy_state_id = p.occupancy_state_id"
                f"{where}",
                params,
            )
            total = (await cursor.fetchone())["total"]
            items = await _completar(cursor, rows)
        return items, int(total)

    async def obtener(self, property_id: int) -> Inmueble | None:
        async with self._db.connection() as conn, conn.cursor(aiomysql.DictCursor) as cursor:
            return await _fetch(cursor, property_id)

    async def crear(self, datos: InmuebleCreate) -> Inmueble:
        async with (
            self._db.transaction() as conn,
            conn.cursor(aiomysql.DictCursor) as cursor,
        ):
            await cursor.execute(
                "INSERT INTO property (address, city_id, registration_identifier, rental_value, "
                "currency_code, occupancy_state_id) VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    datos.direccion,
                    await _ciudad_id(cursor, datos.ciudad),
                    datos.matricula,
                    datos.canon,
                    "COP" if datos.canon is not None else None,
                    await _estado_id(cursor, datos.estado),
                ),
            )
            property_id = int(cursor.lastrowid)
            await _agregar_propietarios(cursor, property_id, datos.propietarios_ids)
            await _guardar_servicios(cursor, property_id, datos.servicios)
            inmueble = await _fetch(cursor, property_id)
        assert inmueble is not None  # noqa: S101 - recién insertado en la misma transacción
        return inmueble

    async def actualizar(self, property_id: int, datos: InmuebleCreate) -> Inmueble | None:
        async with (
            self._db.transaction() as conn,
            conn.cursor(aiomysql.DictCursor) as cursor,
        ):
            await cursor.execute(
                "SELECT property_id FROM property WHERE property_id = %s FOR UPDATE", (property_id,)
            )
            if await cursor.fetchone() is None:
                return None
            await cursor.execute(
                "UPDATE property SET address = %s, city_id = %s, registration_identifier = %s, "
                "rental_value = %s, currency_code = %s, occupancy_state_id = %s "
                "WHERE property_id = %s",
                (
                    datos.direccion,
                    await _ciudad_id(cursor, datos.ciudad),
                    datos.matricula,
                    datos.canon,
                    "COP" if datos.canon is not None else None,
                    await _estado_id(cursor, datos.estado),
                    property_id,
                ),
            )
            marcadores = ",".join(["%s"] * len(datos.propietarios_ids))
            await cursor.execute(
                "DELETE FROM property_owner WHERE property_id = %s "
                f"AND person_id NOT IN ({marcadores})",
                (property_id, *datos.propietarios_ids),
            )
            await cursor.execute(
                "SELECT person_id FROM property_owner WHERE property_id = %s", (property_id,)
            )
            actuales = {row["person_id"] for row in await cursor.fetchall()}
            await _agregar_propietarios(
                cursor, property_id, [p for p in datos.propietarios_ids if p not in actuales]
            )
            await cursor.execute(
                "DELETE FROM property_utility WHERE property_id = %s", (property_id,)
            )
            await _guardar_servicios(cursor, property_id, datos.servicios)
            return await _fetch(cursor, property_id)

    async def contar_contratos(self, property_id: int) -> int:
        async with self._db.connection() as conn, conn.cursor() as cursor:
            await cursor.execute(
                "SELECT COUNT(*) FROM property_agreement WHERE property_id = %s", (property_id,)
            )
            return int((await cursor.fetchone())[0])

    async def eliminar(self, property_id: int) -> bool:
        try:
            async with self._db.transaction() as conn, conn.cursor() as cursor:
                await cursor.execute(
                    "DELETE FROM property_utility WHERE property_id = %s", (property_id,)
                )
                await cursor.execute(
                    "DELETE FROM property_owner WHERE property_id = %s", (property_id,)
                )
                await cursor.execute("DELETE FROM property WHERE property_id = %s", (property_id,))
                return cursor.rowcount > 0
        except pymysql.err.IntegrityError as exc:
            if mysql_error_code(exc) == ER_ROW_IS_REFERENCED:
                raise RegistroReferenciadoError() from exc
            raise


# ── Helpers compartidos (contratos reutiliza propietarios_de) ───────────────────────────────


async def propietarios_de(
    cursor: aiomysql.DictCursor, property_ids: list[int]
) -> dict[int, list[PersonaResumen]]:
    if not property_ids:
        return {}
    marcadores = ",".join(["%s"] * len(property_ids))
    await cursor.execute(PROPIETARIOS_SQL.format(marcadores=marcadores), property_ids)
    por_inmueble: dict[int, list[PersonaResumen]] = defaultdict(list)
    for row in await cursor.fetchall():
        por_inmueble[row["property_id"]].append(persona_resumen(row))
    return por_inmueble


def persona_resumen(row: dict[str, Any]) -> PersonaResumen:
    return PersonaResumen(
        id=row["person_id"],
        nombre=row["full_name"] or "",
        tipo_identificacion=row["tipo_identificacion"],
        identificacion=row["document_identifier"],
        telefono=row["phone_number"],
        correo=row["email_address"],
    )


async def _agregar_propietarios(
    cursor: aiomysql.DictCursor, property_id: int, person_ids: list[int]
) -> None:
    for person_id in person_ids:
        try:
            await cursor.execute(
                "INSERT INTO property_owner (property_id, person_id) VALUES (%s, %s)",
                (property_id, person_id),
            )
        except pymysql.err.IntegrityError as exc:
            if mysql_error_code(exc) == ER_NO_REFERENCED_ROW:
                raise PersonaNoEncontradaError(f"La persona {person_id} no existe.") from exc
            raise
        # Decisión con el responsable: ser propietario de un inmueble agrega el papel.
        await agregar_papeles(cursor, person_id, ["propietario"])


async def _guardar_servicios(
    cursor: aiomysql.DictCursor, property_id: int, servicios: list[ServicioPublicoCreate]
) -> None:
    for servicio in servicios:
        tipo_id = None
        if servicio.tipo:
            await cursor.execute(
                "SELECT utility_type_id FROM utility_type WHERE code = %s", (servicio.tipo,)
            )
            row = await cursor.fetchone()
            if row is None:
                raise CatalogoInvalidoError("servicios.tipo")
            tipo_id = row["utility_type_id"]
        await cursor.execute(
            "INSERT INTO property_utility (property_id, utility_type_id, provider_id, "
            "contract_identifier) VALUES (%s, %s, %s, %s)",
            (
                property_id,
                tipo_id,
                await _proveedor_id(cursor, servicio.proveedor),
                servicio.numero_contrato,
            ),
        )


async def _ciudad_id(cursor: aiomysql.DictCursor, nombre: str | None) -> int | None:
    """Ciudad por nombre exacto; se crea si no existe (decisión: sin pantalla de catálogos)."""
    if not nombre:
        return None
    await cursor.execute(
        "SELECT city_id FROM city WHERE name = %s AND country_code = 'CO'", (nombre,)
    )
    row = await cursor.fetchone()
    if row is not None:
        return int(row["city_id"])
    await cursor.execute("INSERT INTO city (name, country_code) VALUES (%s, 'CO')", (nombre,))
    return int(cursor.lastrowid)


async def _proveedor_id(cursor: aiomysql.DictCursor, nombre: str | None) -> int | None:
    if not nombre:
        return None
    await cursor.execute("SELECT provider_id FROM service_provider WHERE name = %s", (nombre,))
    row = await cursor.fetchone()
    if row is not None:
        return int(row["provider_id"])
    await cursor.execute("INSERT INTO service_provider (name) VALUES (%s)", (nombre,))
    return int(cursor.lastrowid)


async def _estado_id(cursor: aiomysql.DictCursor, codigo: str | None) -> int | None:
    if not codigo:
        return None
    await cursor.execute(
        "SELECT occupancy_state_id FROM occupancy_state WHERE code = %s", (codigo,)
    )
    row = await cursor.fetchone()
    if row is None:
        raise CatalogoInvalidoError("estado")
    return int(row["occupancy_state_id"])


def _where(filtros: InmuebleFiltros) -> tuple[str, list[Any]]:
    where: list[str] = []
    params: list[Any] = []
    if filtros.estado:
        where.append("os.code = %s")
        params.append(filtros.estado.upper())
    if filtros.ciudad:
        where.append("c.name COLLATE utf8mb4_0900_ai_ci LIKE %s")
        params.append(like_pattern(filtros.ciudad))
    if filtros.propietario_id is not None:
        where.append(
            "EXISTS (SELECT 1 FROM property_owner po "
            "WHERE po.property_id = p.property_id AND po.person_id = %s)"
        )
        params.append(filtros.propietario_id)
    if filtros.q:
        where.append(
            "(p.address COLLATE utf8mb4_0900_ai_ci LIKE %s "
            "OR p.registration_identifier COLLATE utf8mb4_0900_ai_ci LIKE %s)"
        )
        params += [like_pattern(filtros.q), like_pattern(filtros.q)]
    return (f" WHERE {' AND '.join(where)}" if where else ""), params


async def _fetch(cursor: aiomysql.DictCursor, property_id: int) -> Inmueble | None:
    await cursor.execute(f"{_SELECT} WHERE p.property_id = %s", (property_id,))
    row = await cursor.fetchone()
    if row is None:
        return None
    return (await _completar(cursor, [row]))[0]


async def _completar(cursor: aiomysql.DictCursor, rows: list[dict[str, Any]]) -> list[Inmueble]:
    ids = [row["property_id"] for row in rows]
    propietarios = await propietarios_de(cursor, ids)
    servicios: dict[int, list[ServicioPublico]] = defaultdict(list)
    if ids:
        await cursor.execute(_SERVICIOS.format(marcadores=",".join(["%s"] * len(ids))), ids)
        for srv in await cursor.fetchall():
            servicios[srv["property_id"]].append(
                ServicioPublico(
                    id=srv["property_utility_id"],
                    tipo=srv["tipo"],
                    proveedor=srv["proveedor"],
                    numero_contrato=srv["contract_identifier"],
                )
            )
    return [
        Inmueble(
            id=row["property_id"],
            direccion=row["address"],
            ciudad=row["ciudad"],
            matricula=row["registration_identifier"],
            canon=row["rental_value"],
            moneda=row["currency_code"],
            estado=row["estado"],
            servicios=servicios.get(row["property_id"], []),
            propietarios=propietarios.get(row["property_id"], []),
            total_contratos=int(row["total_contratos"]),
        )
        for row in rows
    ]
