from __future__ import annotations

from typing import Any, Protocol

from core.errors import ConflictError, NotFoundError
from modules.auth.schemas import Principal
from modules.papelera.schemas import EntradaPapelera, entrada
from modules.personas.schemas import (
    PAPELES,
    Dependencias,
    Papel,
    Persona,
    PersonaCreate,
    PersonaDetalle,
    PersonaFiltros,
    PersonasPage,
)


class PersonaNoEncontradaError(NotFoundError):
    code = "persona_no_encontrada"
    default_message = "La persona no existe."


class PersonaConDependenciasError(ConflictError):
    code = "persona_con_dependencias"
    default_message = "No se puede eliminar: la persona tiene registros asociados."


class PapelEnUsoError(ConflictError):
    code = "papel_en_uso"

    def __init__(self, papel: Papel) -> None:
        super().__init__(
            f"No se puede quitar el papel «{papel}»: la persona tiene registros asociados con "
            "ese papel."
        )


class PersonasRepositoryPort(Protocol):
    async def listar(
        self, filtros: PersonaFiltros, *, limit: int, offset: int
    ) -> tuple[list[Persona], int]: ...

    async def obtener(self, person_id: int) -> Persona | None: ...

    async def buscar_por_identificacion(self, tipo: str, numero: str) -> Persona | None: ...

    async def crear(self, datos: PersonaCreate, papeles: list[Papel]) -> Persona: ...

    async def actualizar(
        self, person_id: int, datos: PersonaCreate, papeles: list[Papel]
    ) -> Persona | None: ...

    async def contar_dependencias(self, person_id: int) -> Dependencias: ...

    async def eliminar(self, person_id: int, papelera: EntradaPapelera) -> bool: ...

    async def detalle(self, person_id: int) -> PersonaDetalle | None: ...


class PersonasService:
    def __init__(self, repository: PersonasRepositoryPort) -> None:
        self._repository = repository

    async def listar(self, filtros: PersonaFiltros, *, limit: int, offset: int) -> PersonasPage:
        items, total = await self._repository.listar(filtros, limit=limit, offset=offset)
        return PersonasPage(items=items, total=total, limit=limit, offset=offset)

    async def obtener(self, person_id: int) -> PersonaDetalle:
        persona = await self._repository.detalle(person_id)
        if persona is None:
            raise PersonaNoEncontradaError()
        return persona

    async def buscar(self, tipo: str, numero: str) -> Persona:
        persona = await self._repository.buscar_por_identificacion(tipo.upper(), numero)
        if persona is None:
            raise PersonaNoEncontradaError()
        return persona

    async def crear(self, datos: PersonaCreate, papel_fijo: Papel | None) -> Persona:
        return await self._repository.crear(datos, _papeles(datos, papel_fijo))

    async def actualizar(
        self, person_id: int, datos: PersonaCreate, papel_fijo: Papel | None
    ) -> Persona:
        actual = await self._repository.obtener(person_id)
        if actual is None:
            raise PersonaNoEncontradaError()
        papeles = _papeles(datos, papel_fijo)
        quitados = [papel for papel in actual.papeles if papel not in papeles]
        if quitados:
            dependencias = await self._repository.contar_dependencias(person_id)
            for papel in quitados:
                if dependencias.por_papel.get(papel, 0) > 0:
                    raise PapelEnUsoError(papel)
        persona = await self._repository.actualizar(person_id, datos, papeles)
        if persona is None:
            raise PersonaNoEncontradaError()
        return persona

    async def eliminar(self, person_id: int, actor: Principal) -> None:
        persona = await self._repository.obtener(person_id)
        if persona is None:
            raise PersonaNoEncontradaError()
        dependencias = await self._repository.contar_dependencias(person_id)
        partes = []
        if dependencias.inmuebles:
            partes.append(f"es propietaria de {dependencias.inmuebles} inmueble(s)")
        if dependencias.contratos:
            partes.append(f"participa en {dependencias.contratos} contrato(s)")
        if dependencias.usuarios:
            partes.append("tiene una cuenta de usuario")
        if partes:
            raise PersonaConDependenciasError("No se puede eliminar: " + ", ".join(partes) + ".")
        descripcion = f"{persona.nombre} ({persona.tipo_identificacion} {persona.identificacion})"
        papelera = entrada("persona", person_id, descripcion, _instantanea(persona), actor)
        if not await self._repository.eliminar(person_id, papelera):
            raise PersonaNoEncontradaError()


def _instantanea(persona: Persona) -> dict[str, Any]:
    """Datos con la forma de ``PersonaCreate`` para restaurarla desde la papelera."""
    datos = persona.model_dump(
        mode="json",
        include={
            "nombre",
            "tipo_identificacion",
            "identificacion",
            "telefono",
            "correo",
            "direccion",
            "papeles",
        },
    )
    cuenta = persona.cuenta_bancaria
    datos["cuenta_bancaria"] = (
        None if cuenta is None else cuenta.model_dump(mode="json", exclude={"id"})
    )
    return datos


def _papeles(datos: PersonaCreate, papel_fijo: Papel | None) -> list[Papel]:
    pedidos = set(datos.papeles) | ({papel_fijo} if papel_fijo else set())
    return [papel for papel in PAPELES if papel in pedidos]
