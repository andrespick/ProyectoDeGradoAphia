# ruff: noqa: S608 - el SQL se arma solo con fragmentos fijos; los valores van parametrizados
from __future__ import annotations

from collections import defaultdict
from typing import Any

import aiomysql
import pymysql

from core.errors import CatalogoInvalidoError, RegistroReferenciadoError
from core.fechas import hoy
from db.connection import Database
from db.sql import (
    ER_NO_REFERENCED_ROW,
    ER_ROW_IS_REFERENCED,
    HOY_SQL,
    like_pattern,
    mysql_error_code,
)
from modules.catalogos.schemas import PAPEL_POR_CODIGO
from modules.contratos.schemas import (
    DIAS_POR_VENCER,
    Contrato,
    ContratoCreate,
    ContratoFiltros,
    estado_de,
)
from modules.inmuebles.repository import PERSONA_JOINS, persona_resumen
from modules.papelera.repository import guardar_en_papelera
from modules.papelera.schemas import EntradaPapelera
from modules.personas.repository import agregar_papeles
from modules.personas.schemas import InmuebleResumen, Papel, PersonaResumen
from modules.personas.service import PersonaNoEncontradaError

_FROM = (
    "FROM property_agreement a "
    "JOIN agreement_category ac ON ac.agreement_category_id = a.agreement_category_id "
    "JOIN property pr ON pr.property_id = a.property_id "
    "LEFT JOIN city c ON c.city_id = pr.city_id "
    "LEFT JOIN occupancy_state os ON os.occupancy_state_id = pr.occupancy_state_id"
)
_SELECT = (
    "SELECT a.agreement_id, ac.code AS tipo, a.start_date, a.end_date, a.agreed_rental_value, "
    "a.currency_code, a.conditions, a.agreement_content, pr.property_id, pr.address, "
    f"c.name AS ciudad, os.code AS estado_inmueble {_FROM}"
)
_PARTES = (
    "SELECT ap.agreement_id, prl.code AS rol, pe.person_id, pe.full_name, "
    "dt.code AS tipo_identificacion, d.document_identifier, ph.phone_number, e.email_address "
    "FROM agreement_party ap JOIN party_role prl ON prl.party_role_id = ap.party_role_id "
    f"JOIN person pe ON pe.person_id = ap.person_id {PERSONA_JOINS} "
    "WHERE ap.agreement_id IN ({marcadores}) ORDER BY pe.full_name"
)
_ESTADOS = {
    "vigente": f"a.start_date <= {HOY_SQL} AND (a.end_date IS NULL OR a.end_date >= {HOY_SQL})",
    "por_vencer": f"a.end_date BETWEEN {HOY_SQL} AND {HOY_SQL} + INTERVAL {DIAS_POR_VENCER} DAY",
    "finalizado": f"a.end_date < {HOY_SQL}",
    "programado": f"a.start_date > {HOY_SQL}",
}


class ContratosRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def listar(
        self, filtros: ContratoFiltros, *, limit: int, offset: int
    ) -> tuple[list[Contrato], int]:
        where, params = _where(filtros)
        async with self._db.connection() as conn, conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                f"{_SELECT}{where} ORDER BY a.start_date DESC, a.agreement_id DESC "
                "LIMIT %s OFFSET %s",
                (*params, limit, offset),
            )
            rows = await cursor.fetchall()
            await cursor.execute(f"SELECT COUNT(*) AS total {_FROM}{where}", params)
            total = (await cursor.fetchone())["total"]
            items = await _completar(cursor, rows)
        return items, int(total)

    async def obtener(self, agreement_id: int) -> Contrato | None:
        async with self._db.connection() as conn, conn.cursor(aiomysql.DictCursor) as cursor:
            return await _fetch(cursor, agreement_id)

    async def propietarios_del_inmueble(self, property_id: int) -> list[int] | None:
        async with self._db.connection() as conn, conn.cursor() as cursor:
            await cursor.execute("SELECT 1 FROM property WHERE property_id = %s", (property_id,))
            if await cursor.fetchone() is None:
                return None
            await cursor.execute(
                "SELECT person_id FROM property_owner WHERE property_id = %s ORDER BY person_id",
                (property_id,),
            )
            return [int(row[0]) for row in await cursor.fetchall()]

    async def crear(self, datos: ContratoCreate, propietarios_ids: list[int]) -> Contrato:
        async with (
            self._db.transaction() as conn,
            conn.cursor(aiomysql.DictCursor) as cursor,
        ):
            await cursor.execute(
                "INSERT INTO property_agreement (agreement_category_id, property_id, start_date, "
                "end_date, agreement_content, conditions, agreed_rental_value, currency_code) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (await _categoria_id(cursor, datos.tipo), *_valores(datos)),
            )
            agreement_id = int(cursor.lastrowid)
            await _insertar_partes(cursor, agreement_id, datos, propietarios_ids)
            contrato = await _fetch(cursor, agreement_id)
        assert contrato is not None  # noqa: S101 - recién insertado en la misma transacción
        return contrato

    async def actualizar(
        self, agreement_id: int, datos: ContratoCreate, propietarios_ids: list[int]
    ) -> Contrato | None:
        async with (
            self._db.transaction() as conn,
            conn.cursor(aiomysql.DictCursor) as cursor,
        ):
            await cursor.execute(
                "SELECT agreement_id FROM property_agreement WHERE agreement_id = %s FOR UPDATE",
                (agreement_id,),
            )
            if await cursor.fetchone() is None:
                return None
            await cursor.execute(
                "UPDATE property_agreement SET agreement_category_id = %s, property_id = %s, "
                "start_date = %s, end_date = %s, agreement_content = %s, conditions = %s, "
                "agreed_rental_value = %s, currency_code = %s WHERE agreement_id = %s",
                (await _categoria_id(cursor, datos.tipo), *_valores(datos), agreement_id),
            )
            await cursor.execute(
                "DELETE FROM agreement_party WHERE agreement_id = %s", (agreement_id,)
            )
            await _insertar_partes(cursor, agreement_id, datos, propietarios_ids)
            return await _fetch(cursor, agreement_id)

    async def contar_dependencias(self, agreement_id: int) -> tuple[int, int]:
        async with self._db.connection() as conn, conn.cursor() as cursor:
            await cursor.execute(
                "SELECT (SELECT COUNT(*) FROM financial_record WHERE agreement_id = %s), "
                "(SELECT COUNT(*) FROM file_agreement WHERE agreement_id = %s)",
                (agreement_id, agreement_id),
            )
            financieros, archivos = await cursor.fetchone()
            return int(financieros), int(archivos)

    async def eliminar(self, agreement_id: int, papelera: EntradaPapelera) -> bool:
        try:
            async with self._db.transaction() as conn, conn.cursor() as cursor:
                await cursor.execute(
                    "DELETE FROM agreement_party WHERE agreement_id = %s", (agreement_id,)
                )
                await cursor.execute(
                    "DELETE FROM property_agreement WHERE agreement_id = %s", (agreement_id,)
                )
                if cursor.rowcount == 0:
                    return False
                await guardar_en_papelera(cursor, papelera)
                return True
        except pymysql.err.IntegrityError as exc:
            if mysql_error_code(exc) == ER_ROW_IS_REFERENCED:
                raise RegistroReferenciadoError() from exc
            raise


def _valores(datos: ContratoCreate) -> tuple[Any, ...]:
    return (
        datos.inmueble_id,
        datos.fecha_inicio,
        datos.fecha_fin,
        datos.texto,
        datos.condiciones,
        datos.canon_pactado,
        "COP" if datos.canon_pactado is not None else None,
    )


async def _categoria_id(cursor: aiomysql.DictCursor, codigo: str) -> int:
    await cursor.execute(
        "SELECT agreement_category_id FROM agreement_category WHERE code = %s", (codigo,)
    )
    row = await cursor.fetchone()
    if row is None:
        raise CatalogoInvalidoError("tipo")
    return int(row["agreement_category_id"])


async def _insertar_partes(
    cursor: aiomysql.DictCursor, agreement_id: int, datos: ContratoCreate, propietarios: list[int]
) -> None:
    partes: list[tuple[int, Papel]] = [(p, "propietario") for p in propietarios]
    if datos.arrendatario_id is not None:
        partes.append((datos.arrendatario_id, "arrendatario"))
    partes += [(c, "codeudor") for c in datos.codeudores_ids]
    for person_id, papel in partes:
        try:
            await cursor.execute(
                "INSERT INTO agreement_party (agreement_id, person_id, party_role_id) "
                "SELECT %s, %s, party_role_id FROM party_role WHERE code = %s",
                (agreement_id, person_id, _CODIGO[papel]),
            )
        except pymysql.err.IntegrityError as exc:
            if mysql_error_code(exc) == ER_NO_REFERENCED_ROW:
                raise PersonaNoEncontradaError(f"La persona {person_id} no existe.") from exc
            raise
        # Decisión con el responsable: participar en un contrato agrega el papel a la persona.
        await agregar_papeles(cursor, person_id, [papel])


_CODIGO = {papel: codigo for codigo, papel in PAPEL_POR_CODIGO.items()}


def _where(filtros: ContratoFiltros) -> tuple[str, list[Any]]:
    where: list[str] = []
    params: list[Any] = []
    if filtros.fecha_desde:  # vigencias que se solapan con [desde, hasta]
        where.append("(a.end_date IS NULL OR a.end_date >= %s)")
        params.append(filtros.fecha_desde)
    if filtros.fecha_hasta:
        where.append("a.start_date <= %s")
        params.append(filtros.fecha_hasta)
    if filtros.inmueble_id is not None:
        where.append("a.property_id = %s")
        params.append(filtros.inmueble_id)
    for person_id, codigo in ((filtros.propietario_id, "OWNER"), (filtros.inquilino_id, "TENANT")):
        if person_id is not None:
            where.append(
                "EXISTS (SELECT 1 FROM agreement_party ap "
                "JOIN party_role prl ON prl.party_role_id = ap.party_role_id "
                "WHERE ap.agreement_id = a.agreement_id AND ap.person_id = %s "
                f"AND prl.code = '{codigo}')"
            )
            params.append(person_id)
    if filtros.tipo:
        where.append("ac.code = %s")
        params.append(filtros.tipo.upper())
    if filtros.estado:
        where.append(_ESTADOS.get(filtros.estado, "FALSE"))
    if filtros.q:
        where.append(
            "(pr.address COLLATE utf8mb4_0900_ai_ci LIKE %s OR EXISTS ("
            "SELECT 1 FROM agreement_party ap JOIN person pe ON pe.person_id = ap.person_id "
            "WHERE ap.agreement_id = a.agreement_id "
            "AND pe.full_name COLLATE utf8mb4_0900_ai_ci LIKE %s))"
        )
        params += [like_pattern(filtros.q), like_pattern(filtros.q)]
    return (f" WHERE {' AND '.join(where)}" if where else ""), params


async def _fetch(cursor: aiomysql.DictCursor, agreement_id: int) -> Contrato | None:
    await cursor.execute(f"{_SELECT} WHERE a.agreement_id = %s", (agreement_id,))
    row = await cursor.fetchone()
    if row is None:
        return None
    return (await _completar(cursor, [row]))[0]


async def _completar(cursor: aiomysql.DictCursor, rows: list[dict[str, Any]]) -> list[Contrato]:
    ids = [row["agreement_id"] for row in rows]
    partes: dict[tuple[int, str], list[PersonaResumen]] = defaultdict(list)
    if ids:
        await cursor.execute(_PARTES.format(marcadores=",".join(["%s"] * len(ids))), ids)
        for parte in await cursor.fetchall():
            partes[(parte["agreement_id"], parte["rol"])].append(persona_resumen(parte))
    dia = hoy()
    contratos = []
    for row in rows:
        estado, dias = estado_de(row["start_date"], row["end_date"], dia)
        arrendatarios = partes.get((row["agreement_id"], "TENANT"), [])
        contratos.append(
            Contrato(
                id=row["agreement_id"],
                tipo=row["tipo"],
                inmueble=InmuebleResumen(
                    id=row["property_id"],
                    direccion=row["address"],
                    ciudad=row["ciudad"],
                    estado=row["estado_inmueble"],
                ),
                fecha_inicio=row["start_date"],
                fecha_fin=row["end_date"],
                canon_pactado=row["agreed_rental_value"],
                moneda=row["currency_code"],
                estado=estado,
                dias_restantes=dias,
                propietarios=partes.get((row["agreement_id"], "OWNER"), []),
                arrendatario=arrendatarios[0] if arrendatarios else None,
                codeudores=partes.get((row["agreement_id"], "CO_DEBTOR"), []),
                condiciones=row["conditions"],
                texto=row["agreement_content"],
            )
        )
    return contratos
