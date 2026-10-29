# ruff: noqa: S608 - tablas y columnas salen de _CATALOGOS (fijo); los valores van parametrizados
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import aiomysql
import pymysql

from core.errors import ConflictError, NotFoundError
from db.connection import Database
from db.sql import ER_DUP_ENTRY, ER_ROW_IS_REFERENCED, mysql_error_code
from modules.auth.schemas import Role
from modules.catalogos.schemas import (
    PAPEL_POR_CODIGO,
    CatalogoAdministrable,
    Catalogos,
    Ciudad,
    ItemCatalogo,
    ItemCatalogoCreate,
    Opcion,
)

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


# ── Administración de catálogos (Administrador de Sistemas) ──────────────────────────────────


class ItemCatalogoNoEncontradoError(NotFoundError):
    code = "catalogo_item_no_encontrado"
    default_message = "El valor no existe en el catálogo."


class CatalogoDuplicadoError(ConflictError):
    code = "catalogo_duplicado"
    default_message = "Ya existe un valor con ese código o nombre en el catálogo."


class CatalogoEnUsoError(ConflictError):
    code = "catalogo_en_uso"

    def __init__(self, en_uso: int) -> None:
        super().__init__(
            f"No se puede eliminar: lo usan {en_uso} registro(s). Puede renombrarlo en su lugar."
        )


@dataclass(frozen=True)
class _Catalogo:
    tabla: str
    id: str
    con_codigo: bool
    # Tablas y columnas que lo referencian (para «en uso» y el mensaje al eliminar).
    usos: tuple[tuple[str, str], ...]
    # Columna fija: filtra la lista y se asigna al crear (p. ej. el ámbito emisor 'CO').
    fija: tuple[str, str] | None = None
    # Solo se asigna al crear (las ciudades nuevas son de Colombia).
    al_crear: tuple[str, str] | None = None


_CATALOGOS: dict[str, _Catalogo] = {
    "tipos-identificacion": _Catalogo(
        "document_type",
        "document_type_id",
        True,
        (("person_document", "document_type_id"),),
        fija=("issuer_scope", "CO"),
    ),
    "tipos-contrato": _Catalogo(
        "agreement_category",
        "agreement_category_id",
        True,
        (("property_agreement", "agreement_category_id"),),
    ),
    "tipos-cuenta-bancaria": _Catalogo(
        "bank_account_category",
        "bank_account_category_id",
        True,
        (("bank_account", "bank_account_category_id"),),
    ),
    "tipos-servicio": _Catalogo(
        "utility_type", "utility_type_id", True, (("property_utility", "utility_type_id"),)
    ),
    "ciudades": _Catalogo(
        "city",
        "city_id",
        False,
        (("property", "city_id"), ("organization_profile", "city_id")),
        al_crear=("country_code", "CO"),
    ),
    "bancos": _Catalogo(
        "financial_institution",
        "financial_institution_id",
        False,
        (("bank_account", "financial_institution_id"),),
    ),
    "proveedores-servicios": _Catalogo(
        "service_provider", "provider_id", False, (("property_utility", "provider_id"),)
    ),
}


class CatalogosAdminRepositoryPort(Protocol):
    async def listar(self, catalogo: CatalogoAdministrable) -> list[ItemCatalogo]: ...

    async def crear(
        self, catalogo: CatalogoAdministrable, datos: ItemCatalogoCreate
    ) -> ItemCatalogo: ...

    async def renombrar(
        self, catalogo: CatalogoAdministrable, item_id: int, nombre: str
    ) -> ItemCatalogo: ...

    async def eliminar(self, catalogo: CatalogoAdministrable, item_id: int) -> None: ...


class CatalogosAdminRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def listar(self, catalogo: CatalogoAdministrable) -> list[ItemCatalogo]:
        definicion = _CATALOGOS[catalogo]
        where, params = _filtro(definicion)
        async with self._db.connection() as conn, conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(f"{_select(definicion)}{where} ORDER BY t.name", params)
            return [_item(row) for row in await cursor.fetchall()]

    async def crear(
        self, catalogo: CatalogoAdministrable, datos: ItemCatalogoCreate
    ) -> ItemCatalogo:
        definicion = _CATALOGOS[catalogo]
        columnas = ["name"]
        valores: list[Any] = [datos.nombre]
        if definicion.con_codigo:
            columnas.append("code")
            valores.append(datos.codigo)
        for extra in (definicion.fija, definicion.al_crear):
            if extra:
                columnas.append(extra[0])
                valores.append(extra[1])
        try:
            async with (
                self._db.transaction() as conn,
                conn.cursor(aiomysql.DictCursor) as cursor,
            ):
                await _exigir_nombre_libre(cursor, definicion, datos.nombre, excepto=None)
                marcadores = ", ".join(["%s"] * len(valores))
                await cursor.execute(
                    f"INSERT INTO {definicion.tabla} ({', '.join(columnas)}) VALUES ({marcadores})",
                    valores,
                )
                item = await _fetch(cursor, definicion, int(cursor.lastrowid))
        except pymysql.err.IntegrityError as exc:
            if mysql_error_code(exc) == ER_DUP_ENTRY:
                raise CatalogoDuplicadoError() from exc
            raise
        assert item is not None  # noqa: S101 - recién insertado en la misma transacción
        return item

    async def renombrar(
        self, catalogo: CatalogoAdministrable, item_id: int, nombre: str
    ) -> ItemCatalogo:
        definicion = _CATALOGOS[catalogo]
        async with self._db.transaction() as conn, conn.cursor(aiomysql.DictCursor) as cursor:
            if await _fetch(cursor, definicion, item_id) is None:
                raise ItemCatalogoNoEncontradoError()
            await _exigir_nombre_libre(cursor, definicion, nombre, excepto=item_id)
            await cursor.execute(
                f"UPDATE {definicion.tabla} SET name = %s WHERE {definicion.id} = %s",
                (nombre, item_id),
            )
            item = await _fetch(cursor, definicion, item_id)
        assert item is not None  # noqa: S101 - comprobado arriba en la misma transacción
        return item

    async def eliminar(self, catalogo: CatalogoAdministrable, item_id: int) -> None:
        definicion = _CATALOGOS[catalogo]
        try:
            async with (
                self._db.transaction() as conn,
                conn.cursor(aiomysql.DictCursor) as cursor,
            ):
                item = await _fetch(cursor, definicion, item_id)
                if item is None:
                    raise ItemCatalogoNoEncontradoError()
                if item.en_uso:
                    raise CatalogoEnUsoError(item.en_uso)
                await cursor.execute(
                    f"DELETE FROM {definicion.tabla} WHERE {definicion.id} = %s", (item_id,)
                )
        except pymysql.err.IntegrityError as exc:
            # Lo referenció otro registro entre la consulta y el borrado.
            if mysql_error_code(exc) == ER_ROW_IS_REFERENCED:
                raise CatalogoEnUsoError(1) from exc
            raise


def _select(definicion: _Catalogo) -> str:
    usos = " + ".join(
        f"(SELECT COUNT(*) FROM {tabla} u WHERE u.{columna} = t.{definicion.id})"
        for tabla, columna in definicion.usos
    )
    codigo = "t.code" if definicion.con_codigo else "NULL"
    return (
        f"SELECT t.{definicion.id} AS id, {codigo} AS codigo, t.name AS nombre, "
        f"({usos}) AS en_uso FROM {definicion.tabla} t"
    )


def _filtro(definicion: _Catalogo) -> tuple[str, list[Any]]:
    if definicion.fija is None:
        return "", []
    return f" WHERE t.{definicion.fija[0]} = %s", [definicion.fija[1]]


async def _fetch(
    cursor: aiomysql.DictCursor, definicion: _Catalogo, item_id: int
) -> ItemCatalogo | None:
    where, params = _filtro(definicion)
    condicion = f"{where} AND" if where else " WHERE"
    await cursor.execute(
        f"{_select(definicion)}{condicion} t.{definicion.id} = %s", (*params, item_id)
    )
    row = await cursor.fetchone()
    return None if row is None else _item(row)


async def _exigir_nombre_libre(
    cursor: aiomysql.DictCursor, definicion: _Catalogo, nombre: str, excepto: int | None
) -> None:
    """Los catálogos de nombre libre se buscan por nombre exacto: un duplicado sería ambiguo."""
    if definicion.con_codigo:
        return
    await cursor.execute(
        f"SELECT 1 FROM {definicion.tabla} WHERE name = %s AND {definicion.id} <> %s LIMIT 1",
        (nombre, excepto or 0),
    )
    if await cursor.fetchone() is not None:
        raise CatalogoDuplicadoError()


def _item(row: dict[str, Any]) -> ItemCatalogo:
    return ItemCatalogo(
        id=row["id"], codigo=row["codigo"], nombre=row["nombre"], en_uso=int(row["en_uso"])
    )
