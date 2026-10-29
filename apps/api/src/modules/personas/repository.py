# ruff: noqa: S608 - el SQL se arma solo con fragmentos fijos; los valores van parametrizados
from __future__ import annotations

from typing import Any

import aiomysql
import pymysql

from core.errors import (
    CatalogoInvalidoError,
    IdentificacionDuplicadaError,
    RegistroReferenciadoError,
)
from db.connection import Database
from db.sql import ER_DUP_ENTRY, ER_ROW_IS_REFERENCED, like_pattern, mysql_error_code
from modules.catalogos.schemas import PAPEL_POR_CODIGO
from modules.papelera.repository import guardar_en_papelera
from modules.papelera.schemas import EntradaPapelera
from modules.personas.schemas import (
    ContratoResumen,
    CuentaBancaria,
    Dependencias,
    InmuebleResumen,
    Papel,
    Persona,
    PersonaCreate,
    PersonaDetalle,
    PersonaFiltros,
    codigo_de,
)

TIPO_DOCUMENTO_SQL = (
    "SELECT document_type_id FROM document_type WHERE issuer_scope = 'CO' AND code = %s"
)
PAPEL_SQL = "SELECT party_role_id FROM party_role WHERE code = %s"

# Una fila hija por campo del formulario: se toma la de menor id si hubiera varias (datos migrados).
_SELECT = (
    "SELECT p.person_id, p.full_name, p.address, "
    "dt.code AS tipo_identificacion, d.document_identifier, ph.phone_number, e.email_address, "
    "(SELECT GROUP_CONCAT(pr.code) FROM person_party_role ppr "
    " JOIN party_role pr ON pr.party_role_id = ppr.party_role_id "
    " WHERE ppr.person_id = p.person_id) AS papeles, "
    "(SELECT COUNT(*) FROM property_owner po WHERE po.person_id = p.person_id) AS total_inmuebles, "
    "ba.account_id AS cuenta_id, ba.account_identifier, bac.code AS cuenta_tipo, fi.name AS banco "
    "FROM person p "
    "LEFT JOIN person_document d ON d.person_document_id = "
    " (SELECT MIN(person_document_id) FROM person_document WHERE person_id = p.person_id) "
    "LEFT JOIN document_type dt ON dt.document_type_id = d.document_type_id "
    "LEFT JOIN person_phone ph ON ph.phone_id = "
    " (SELECT MIN(phone_id) FROM person_phone WHERE person_id = p.person_id) "
    "LEFT JOIN person_email e ON e.email_id = "
    " (SELECT MIN(email_id) FROM person_email WHERE person_id = p.person_id) "
    "LEFT JOIN bank_account ba ON ba.account_id = "
    " (SELECT MIN(account_id) FROM bank_account WHERE person_id = p.person_id) "
    "LEFT JOIN bank_account_category bac "
    " ON bac.bank_account_category_id = ba.bank_account_category_id "
    "LEFT JOIN financial_institution fi "
    " ON fi.financial_institution_id = ba.financial_institution_id"
)
_CONTRATOS = (
    "SELECT prl.code AS rol, a.agreement_id, ac.code AS tipo, a.start_date, a.end_date, "
    "pr.property_id, pr.address, c.name AS ciudad, os.code AS estado "
    "FROM agreement_party ap "
    "JOIN party_role prl ON prl.party_role_id = ap.party_role_id "
    "JOIN property_agreement a ON a.agreement_id = ap.agreement_id "
    "JOIN agreement_category ac ON ac.agreement_category_id = a.agreement_category_id "
    "JOIN property pr ON pr.property_id = a.property_id "
    "LEFT JOIN city c ON c.city_id = pr.city_id "
    "LEFT JOIN occupancy_state os ON os.occupancy_state_id = pr.occupancy_state_id "
    "WHERE ap.person_id = %s ORDER BY a.start_date DESC, a.agreement_id DESC"
)
_INMUEBLES = (
    "SELECT pr.property_id, pr.address, c.name AS ciudad, os.code AS estado "
    "FROM property_owner po JOIN property pr ON pr.property_id = po.property_id "
    "LEFT JOIN city c ON c.city_id = pr.city_id "
    "LEFT JOIN occupancy_state os ON os.occupancy_state_id = pr.occupancy_state_id "
    "WHERE po.person_id = %s ORDER BY pr.property_id DESC"
)
_DEPENDENCIAS = (
    "SELECT (SELECT COUNT(*) FROM property_owner WHERE person_id = %s) AS inmuebles, "
    "(SELECT COUNT(DISTINCT agreement_id) FROM agreement_party WHERE person_id = %s) AS contratos, "
    "(SELECT COUNT(*) FROM user_account WHERE person_id = %s) AS usuarios, "
    "(SELECT COUNT(*) FROM agreement_party ap "
    " JOIN party_role pr ON pr.party_role_id = ap.party_role_id "
    " WHERE ap.person_id = %s AND pr.code = 'TENANT') AS como_arrendatario, "
    "(SELECT COUNT(*) FROM agreement_party ap "
    " JOIN party_role pr ON pr.party_role_id = ap.party_role_id "
    " WHERE ap.person_id = %s AND pr.code = 'CO_DEBTOR') AS como_codeudor"
)


class PersonasRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def listar(
        self, filtros: PersonaFiltros, *, limit: int, offset: int
    ) -> tuple[list[Persona], int]:
        where, params = _where(filtros)
        async with self._db.connection() as conn, conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                f"{_SELECT}{where} ORDER BY p.person_id DESC LIMIT %s OFFSET %s",
                (*params, limit, offset),
            )
            rows = await cursor.fetchall()
            await cursor.execute(
                "SELECT COUNT(*) AS total FROM person p "
                "LEFT JOIN person_document d ON d.person_document_id = "
                " (SELECT MIN(person_document_id) FROM person_document "
                "  WHERE person_id = p.person_id) "
                "LEFT JOIN person_email e ON e.email_id = "
                f" (SELECT MIN(email_id) FROM person_email WHERE person_id = p.person_id){where}",
                params,
            )
            total = (await cursor.fetchone())["total"]
        return [_persona(row) for row in rows], int(total)

    async def obtener(self, person_id: int) -> Persona | None:
        async with self._db.connection() as conn, conn.cursor(aiomysql.DictCursor) as cursor:
            return await _fetch(cursor, person_id)

    async def buscar_por_identificacion(self, tipo: str, numero: str) -> Persona | None:
        async with self._db.connection() as conn, conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                f"{_SELECT} WHERE dt.code = %s AND d.document_identifier = %s", (tipo, numero)
            )
            row = await cursor.fetchone()
        return None if row is None else _persona(row)

    async def crear(self, datos: PersonaCreate, papeles: list[Papel]) -> Persona:
        try:
            async with (
                self._db.transaction() as conn,
                conn.cursor(aiomysql.DictCursor) as cursor,
            ):
                await cursor.execute(
                    "INSERT INTO person (full_name, address) VALUES (%s, %s)",
                    (datos.nombre, datos.direccion),
                )
                person_id = int(cursor.lastrowid)
                await guardar_documento(
                    cursor, person_id, datos.tipo_identificacion, datos.identificacion
                )
                await _guardar_contacto(cursor, person_id, datos)
                await agregar_papeles(cursor, person_id, papeles)
                await _guardar_cuenta(cursor, person_id, datos)
                persona = await _fetch(cursor, person_id)
        except pymysql.err.IntegrityError as exc:
            if mysql_error_code(exc) == ER_DUP_ENTRY:
                raise IdentificacionDuplicadaError() from exc
            raise
        assert persona is not None  # noqa: S101 - recién insertada en la misma transacción
        return persona

    async def actualizar(
        self, person_id: int, datos: PersonaCreate, papeles: list[Papel]
    ) -> Persona | None:
        try:
            async with (
                self._db.transaction() as conn,
                conn.cursor(aiomysql.DictCursor) as cursor,
            ):
                await cursor.execute(
                    "SELECT person_id FROM person WHERE person_id = %s FOR UPDATE", (person_id,)
                )
                if await cursor.fetchone() is None:
                    return None
                await cursor.execute(
                    "UPDATE person SET full_name = %s, address = %s WHERE person_id = %s",
                    (datos.nombre, datos.direccion, person_id),
                )
                await guardar_documento(
                    cursor, person_id, datos.tipo_identificacion, datos.identificacion
                )
                await cursor.execute("DELETE FROM person_phone WHERE person_id = %s", (person_id,))
                await cursor.execute("DELETE FROM person_email WHERE person_id = %s", (person_id,))
                await _guardar_contacto(cursor, person_id, datos)
                await agregar_papeles(cursor, person_id, papeles)
                marcadores = ",".join(["%s"] * len(papeles))
                await cursor.execute(
                    "DELETE FROM person_party_role WHERE person_id = %s AND party_role_id NOT IN "
                    f"(SELECT party_role_id FROM party_role WHERE code IN ({marcadores}))",
                    (person_id, *[codigo_de(p) for p in papeles]),
                )
                await cursor.execute("DELETE FROM bank_account WHERE person_id = %s", (person_id,))
                await _guardar_cuenta(cursor, person_id, datos)
                return await _fetch(cursor, person_id)
        except pymysql.err.IntegrityError as exc:
            if mysql_error_code(exc) == ER_DUP_ENTRY:
                raise IdentificacionDuplicadaError() from exc
            raise

    async def contar_dependencias(self, person_id: int) -> Dependencias:
        async with self._db.connection() as conn, conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(_DEPENDENCIAS, (person_id,) * 5)
            row = await cursor.fetchone()
        return Dependencias(
            inmuebles=int(row["inmuebles"]),
            contratos=int(row["contratos"]),
            usuarios=int(row["usuarios"]),
            por_papel={
                "propietario": int(row["inmuebles"]),
                "arrendatario": int(row["como_arrendatario"]),
                "codeudor": int(row["como_codeudor"]),
            },
        )

    async def eliminar(self, person_id: int, papelera: EntradaPapelera) -> bool:
        try:
            async with self._db.transaction() as conn, conn.cursor() as cursor:
                for tabla in (
                    "bank_account",
                    "person_party_role",
                    "person_email",
                    "person_phone",
                    "person_document",
                ):
                    await cursor.execute(f"DELETE FROM {tabla} WHERE person_id = %s", (person_id,))
                await cursor.execute("DELETE FROM person WHERE person_id = %s", (person_id,))
                if cursor.rowcount == 0:
                    return False
                await guardar_en_papelera(cursor, papelera)
                return True
        except pymysql.err.IntegrityError as exc:
            if mysql_error_code(exc) == ER_ROW_IS_REFERENCED:
                raise RegistroReferenciadoError() from exc
            raise

    async def detalle(self, person_id: int) -> PersonaDetalle | None:
        async with self._db.connection() as conn, conn.cursor(aiomysql.DictCursor) as cursor:
            persona = await _fetch(cursor, person_id)
            if persona is None:
                return None
            await cursor.execute(_INMUEBLES, (person_id,))
            inmuebles = [_inmueble(row) for row in await cursor.fetchall()]
            await cursor.execute(_CONTRATOS, (person_id,))
            contratos = await cursor.fetchall()
            await cursor.execute(
                "SELECT user_name FROM user_account WHERE person_id = %s "
                "ORDER BY account_id LIMIT 1",
                (person_id,),
            )
            usuario = await cursor.fetchone()
        por_rol: dict[str, list[ContratoResumen]] = {"OWNER": [], "TENANT": [], "CO_DEBTOR": []}
        for row in contratos:
            por_rol.setdefault(row["rol"], []).append(
                ContratoResumen(
                    id=row["agreement_id"],
                    tipo=row["tipo"],
                    fecha_inicio=row["start_date"],
                    fecha_fin=row["end_date"],
                    inmueble=_inmueble(row),
                )
            )
        return PersonaDetalle(
            **persona.model_dump(),
            inmuebles=inmuebles,
            contratos_como_propietario=por_rol["OWNER"],
            contratos_como_arrendatario=por_rol["TENANT"],
            contratos_como_codeudor=por_rol["CO_DEBTOR"],
            usuario=None if usuario is None else usuario["user_name"],
        )


# ── Helpers compartidos con otros módulos (usuarios, inmuebles, contratos) ──────────────────


async def buscar_persona_id(cursor: aiomysql.DictCursor, tipo: str, numero: str) -> int | None:
    await cursor.execute(
        "SELECT d.person_id FROM person_document d "
        "JOIN document_type dt ON dt.document_type_id = d.document_type_id "
        "WHERE dt.issuer_scope = 'CO' AND dt.code = %s AND d.document_identifier = %s",
        (tipo, numero),
    )
    row = await cursor.fetchone()
    return None if row is None else int(row["person_id"])


async def guardar_documento(
    cursor: aiomysql.DictCursor, person_id: int, tipo: str, numero: str
) -> None:
    """Crea o reemplaza el documento principal de la persona (1062 si lo tiene otra persona)."""
    await cursor.execute(TIPO_DOCUMENTO_SQL, (tipo,))
    row = await cursor.fetchone()
    if row is None:
        raise CatalogoInvalidoError("tipo_identificacion")
    await cursor.execute(
        "UPDATE person_document SET document_type_id = %s, document_identifier = %s "
        "WHERE person_document_id = (SELECT id FROM (SELECT MIN(person_document_id) AS id "
        "FROM person_document WHERE person_id = %s) AS x)",
        (row["document_type_id"], numero, person_id),
    )
    await cursor.execute("SELECT 1 FROM person_document WHERE person_id = %s LIMIT 1", (person_id,))
    if await cursor.fetchone() is None:
        await cursor.execute(
            "INSERT INTO person_document (person_id, document_type_id, document_identifier) "
            "VALUES (%s, %s, %s)",
            (person_id, row["document_type_id"], numero),
        )


async def agregar_papeles(
    cursor: aiomysql.DictCursor, person_id: int, papeles: list[Papel]
) -> None:
    """Papeles declarados; omite los que ya existen (asociaciones automáticas previas)."""
    for papel in papeles:
        await cursor.execute(
            "INSERT INTO person_party_role (person_id, party_role_id) "
            "SELECT %s, pr.party_role_id FROM party_role pr WHERE pr.code = %s "
            "AND NOT EXISTS (SELECT 1 FROM person_party_role ppr "
            " WHERE ppr.person_id = %s AND ppr.party_role_id = pr.party_role_id)",
            (person_id, codigo_de(papel), person_id),
        )


async def _guardar_contacto(
    cursor: aiomysql.DictCursor, person_id: int, datos: PersonaCreate
) -> None:
    if datos.telefono:
        await cursor.execute(
            "INSERT INTO person_phone (person_id, phone_prefix, phone_number) "
            "VALUES (%s, NULL, %s)",
            (person_id, datos.telefono),
        )
    if datos.correo:
        await cursor.execute(
            "INSERT INTO person_email (person_id, email_address) VALUES (%s, %s)",
            (person_id, datos.correo),
        )


async def _guardar_cuenta(
    cursor: aiomysql.DictCursor, person_id: int, datos: PersonaCreate
) -> None:
    cuenta = datos.cuenta_bancaria
    if cuenta is None:
        return
    await cursor.execute(
        "SELECT financial_institution_id FROM financial_institution WHERE name = %s",
        (cuenta.banco,),
    )
    row = await cursor.fetchone()
    if row is None:
        await cursor.execute(
            "INSERT INTO financial_institution (name) VALUES (%s)", (cuenta.banco,)
        )
        banco_id = cursor.lastrowid
    else:
        banco_id = row["financial_institution_id"]
    await cursor.execute(
        "INSERT INTO bank_account (person_id, account_identifier, bank_account_category_id, "
        "financial_institution_id) SELECT %s, %s, bank_account_category_id, %s "
        "FROM bank_account_category WHERE code = %s",
        (person_id, cuenta.numero, banco_id, cuenta.tipo),
    )
    if cursor.rowcount == 0:
        raise CatalogoInvalidoError("cuenta_bancaria.tipo")


def _where(filtros: PersonaFiltros) -> tuple[str, list[Any]]:
    where: list[str] = []
    params: list[Any] = []
    if filtros.solo_con_papel:
        where.append("EXISTS (SELECT 1 FROM person_party_role WHERE person_id = p.person_id)")
    if filtros.papel:
        where.append(
            "EXISTS (SELECT 1 FROM person_party_role ppr "
            "JOIN party_role pr ON pr.party_role_id = ppr.party_role_id "
            "WHERE ppr.person_id = p.person_id AND pr.code = %s)"
        )
        params.append(codigo_de(filtros.papel))
    if filtros.q:
        where.append(
            "(p.full_name COLLATE utf8mb4_0900_ai_ci LIKE %s OR d.document_identifier LIKE %s)"
        )
        params += [like_pattern(filtros.q), like_pattern(filtros.q)]
    if filtros.correo:
        where.append("e.email_address COLLATE utf8mb4_0900_ai_ci LIKE %s")
        params.append(like_pattern(filtros.correo))
    if filtros.contrato_id is not None:
        where.append(
            "EXISTS (SELECT 1 FROM agreement_party ap "
            "JOIN party_role pr ON pr.party_role_id = ap.party_role_id "
            "WHERE ap.person_id = p.person_id AND ap.agreement_id = %s AND pr.code = 'CO_DEBTOR')"
        )
        params.append(filtros.contrato_id)
    return (f" WHERE {' AND '.join(where)}" if where else ""), params


async def _fetch(cursor: aiomysql.DictCursor, person_id: int) -> Persona | None:
    await cursor.execute(f"{_SELECT} WHERE p.person_id = %s", (person_id,))
    row = await cursor.fetchone()
    return None if row is None else _persona(row)


def _persona(row: dict[str, Any]) -> Persona:
    codigos = (row["papeles"] or "").split(",")
    cuenta = (
        CuentaBancaria(
            id=row["cuenta_id"],
            banco=row["banco"],
            tipo=row["cuenta_tipo"],
            numero=row["account_identifier"],
        )
        if row["cuenta_id"] is not None
        else None
    )
    return Persona(
        id=row["person_id"],
        nombre=row["full_name"] or "",
        tipo_identificacion=row["tipo_identificacion"],
        identificacion=row["document_identifier"],
        telefono=row["phone_number"],
        correo=row["email_address"],
        direccion=row["address"],
        papeles=[PAPEL_POR_CODIGO[c] for c in PAPEL_POR_CODIGO if c in codigos],  # type: ignore[misc]
        cuenta_bancaria=cuenta,
        total_inmuebles=int(row["total_inmuebles"]),
    )


def _inmueble(row: dict[str, Any]) -> InmuebleResumen:
    return InmuebleResumen(
        id=row["property_id"], direccion=row["address"], ciudad=row["ciudad"], estado=row["estado"]
    )
