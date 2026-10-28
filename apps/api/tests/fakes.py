"""Repositorios en memoria para pruebas unitarias (sin MySQL)."""

from __future__ import annotations

from datetime import UTC, datetime

from modules.catalogos.schemas import Catalogos, Ciudad, Opcion
from modules.clientes.schemas import Cliente
from modules.clientes.service import CorreoDuplicadoError


class InMemoryClientesRepository:
    def __init__(self) -> None:
        self.items: list[Cliente] = []

    async def listar(self, *, limit: int, offset: int) -> tuple[list[Cliente], int]:
        ordered = sorted(self.items, key=lambda c: c.id, reverse=True)
        return ordered[offset : offset + limit], len(self.items)

    async def crear(self, *, nombre: str, correo: str) -> Cliente:
        if any(c.correo == correo for c in self.items):
            raise CorreoDuplicadoError()
        now = datetime.now(UTC)
        cliente = Cliente(
            id=len(self.items) + 1, nombre=nombre, correo=correo, creado_en=now, actualizado_en=now
        )
        self.items.append(cliente)
        return cliente


CATALOGOS_DE_PRUEBA = Catalogos(
    tipos_identificacion=[
        Opcion(codigo="CC", nombre="Cédula de ciudadanía"),
        Opcion(codigo="NIT", nombre="NIT"),
    ],
    papeles=[
        Opcion(codigo="propietario", nombre="Propietario"),
        Opcion(codigo="arrendatario", nombre="Arrendatario"),
        Opcion(codigo="codeudor", nombre="Codeudor"),
    ],
    roles=[
        Opcion(codigo="admin_sistemas", nombre="Administrador de Sistemas"),
        Opcion(codigo="administrativo", nombre="Administrativo"),
        Opcion(codigo="asesor", nombre="Asesor"),
    ],
    estados_ocupacion=[
        Opcion(codigo="DISPONIBLE", nombre="Disponible"),
        Opcion(codigo="OCUPADO", nombre="Ocupado"),
    ],
    tipos_contrato=[Opcion(codigo="ARRENDAMIENTO", nombre="Arrendamiento")],
    tipos_cuenta_bancaria=[
        Opcion(codigo="AHORROS", nombre="Ahorros"),
        Opcion(codigo="CORRIENTE", nombre="Corriente"),
    ],
    tipos_servicio=[
        Opcion(codigo="AGUA", nombre="Acueducto y alcantarillado"),
        Opcion(codigo="ENERGIA", nombre="Energía"),
    ],
    monedas=[Opcion(codigo="COP", nombre="Peso colombiano")],
    ciudades=[Ciudad(id=9001, nombre="Bogotá")],
    bancos=["Bancolombia"],
    proveedores_servicios=["EPM"],
)


class InMemoryCatalogosRepository:
    def __init__(self, catalogos: Catalogos = CATALOGOS_DE_PRUEBA) -> None:
        self.catalogos = catalogos

    async def obtener(self) -> Catalogos:
        return self.catalogos
