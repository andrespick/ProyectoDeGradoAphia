# ruff: noqa: S608 - el SQL se arma solo con fragmentos fijos; los valores van parametrizados
from __future__ import annotations

import aiomysql

from db.connection import Database
from db.sql import like_pattern
from modules.buscar.schemas import LIMITE_POR_GRUPO, ResultadosBusqueda
from modules.inmuebles.repository import PERSONA_JOINS, persona_resumen
from modules.personas.schemas import ContratoResumen, InmuebleResumen

_AI = "COLLATE utf8mb4_0900_ai_ci LIKE %s"
_PERSONAS = (
    "SELECT pe.person_id, pe.full_name, dt.code AS tipo_identificacion, d.document_identifier, "
    f"ph.phone_number, e.email_address FROM person pe {PERSONA_JOINS} "
    f"WHERE pe.full_name {_AI} OR d.document_identifier LIKE %s "
    f"ORDER BY pe.full_name LIMIT {LIMITE_POR_GRUPO}"
)
_INMUEBLES = (
    "SELECT pr.property_id, pr.address, c.name AS ciudad, os.code AS estado FROM property pr "
    "LEFT JOIN city c ON c.city_id = pr.city_id "
    "LEFT JOIN occupancy_state os ON os.occupancy_state_id = pr.occupancy_state_id "
    f"WHERE pr.address {_AI} OR pr.registration_identifier {_AI} "
    f"ORDER BY pr.property_id DESC LIMIT {LIMITE_POR_GRUPO}"
)
_CONTRATOS = (
    "SELECT a.agreement_id, ac.code AS tipo, a.start_date, a.end_date, pr.property_id, "
    "pr.address, c.name AS ciudad, os.code AS estado FROM property_agreement a "
    "JOIN agreement_category ac ON ac.agreement_category_id = a.agreement_category_id "
    "JOIN property pr ON pr.property_id = a.property_id "
    "LEFT JOIN city c ON c.city_id = pr.city_id "
    "LEFT JOIN occupancy_state os ON os.occupancy_state_id = pr.occupancy_state_id "
    f"WHERE pr.address {_AI} OR EXISTS (SELECT 1 FROM agreement_party ap "
    "JOIN person pe ON pe.person_id = ap.person_id WHERE ap.agreement_id = a.agreement_id "
    f"AND pe.full_name {_AI}) ORDER BY a.start_date DESC, a.agreement_id DESC "
    f"LIMIT {LIMITE_POR_GRUPO}"
)


class BuscarRepository:
    def __init__(self, db: Database) -> None:
        self._db = db

    async def buscar(self, q: str) -> ResultadosBusqueda:
        patron = like_pattern(q)
        async with self._db.connection() as conn, conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(_PERSONAS, (patron, patron))
            personas = [persona_resumen(row) for row in await cursor.fetchall()]
            await cursor.execute(_INMUEBLES, (patron, patron))
            inmuebles = [_inmueble(row) for row in await cursor.fetchall()]
            await cursor.execute(_CONTRATOS, (patron, patron))
            contratos = [
                ContratoResumen(
                    id=row["agreement_id"],
                    tipo=row["tipo"],
                    fecha_inicio=row["start_date"],
                    fecha_fin=row["end_date"],
                    inmueble=_inmueble(row),
                )
                for row in await cursor.fetchall()
            ]
        return ResultadosBusqueda(personas=personas, inmuebles=inmuebles, contratos=contratos)


def _inmueble(row: dict[str, object]) -> InmuebleResumen:
    return InmuebleResumen(
        id=row["property_id"],  # type: ignore[arg-type]
        direccion=row["address"],  # type: ignore[arg-type]
        ciudad=row["ciudad"],  # type: ignore[arg-type]
        estado=row["estado"],  # type: ignore[arg-type]
    )
