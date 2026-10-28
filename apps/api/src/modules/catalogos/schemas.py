from __future__ import annotations

from pydantic import BaseModel

# Papel de una persona: código del catálogo ``party_role`` ↔ nombre que expone la API.
PAPEL_POR_CODIGO = {"OWNER": "propietario", "TENANT": "arrendatario", "CO_DEBTOR": "codeudor"}
CODIGO_POR_PAPEL = {papel: codigo for codigo, papel in PAPEL_POR_CODIGO.items()}


class Opcion(BaseModel):
    codigo: str
    nombre: str


class Ciudad(BaseModel):
    id: int
    nombre: str


class Catalogos(BaseModel):
    tipos_identificacion: list[Opcion]
    papeles: list[Opcion]
    roles: list[Opcion]
    estados_ocupacion: list[Opcion]
    tipos_contrato: list[Opcion]
    tipos_cuenta_bancaria: list[Opcion]
    tipos_servicio: list[Opcion]
    monedas: list[Opcion]
    ciudades: list[Ciudad]
    bancos: list[str]
    proveedores_servicios: list[str]
