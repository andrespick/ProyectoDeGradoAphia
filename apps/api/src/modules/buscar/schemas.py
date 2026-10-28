from __future__ import annotations

from pydantic import BaseModel

from modules.personas.schemas import ContratoResumen, InmuebleResumen, PersonaResumen

LIMITE_POR_GRUPO = 5


class ResultadosBusqueda(BaseModel):
    personas: list[PersonaResumen]
    inmuebles: list[InmuebleResumen]
    contratos: list[ContratoResumen]
