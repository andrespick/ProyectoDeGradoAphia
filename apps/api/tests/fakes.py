"""Repositorios en memoria para pruebas unitarias (sin MySQL)."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

from core.errors import IdentificacionDuplicadaError
from modules.auth.passwords import hash_password
from modules.auth.repository import CuentaLogin
from modules.auth.schemas import Role
from modules.catalogos.schemas import Catalogos, Ciudad, Opcion
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
)
from modules.resumen.schemas import (
    Resumen,
    ResumenContratos,
    ResumenInmuebles,
    ResumenPersonas,
    ResumenUsuarios,
)
from modules.usuarios.repository import UsuarioDuplicadoError
from modules.usuarios.schemas import EstadoUsuario, Usuario, UsuarioCreate, UsuarioUpdate

# Pocas iteraciones para que las pruebas sean rápidas; el formato es el mismo.
ITERACIONES_PRUEBA = 1_000


class InMemoryPersonasRepository:
    def __init__(self) -> None:
        self.items: dict[int, Persona] = {}
        self.dependencias: dict[int, Dependencias] = {}
        self.inmuebles: dict[int, list[InmuebleResumen]] = {}
        self.contratos: dict[int, dict[str, list[ContratoResumen]]] = {}
        self.usuarios: dict[int, str] = {}
        self.codeudores_por_contrato: dict[int, set[int]] = {}

    def agregar(
        self,
        nombre: str,
        identificacion: str,
        papeles: list[Papel],
        *,
        tipo: str = "CC",
        correo: str | None = None,
        telefono: str | None = None,
        total_inmuebles: int = 0,
    ) -> Persona:
        person_id = len(self.items) + 1
        persona = Persona(
            id=person_id,
            nombre=nombre,
            tipo_identificacion=tipo,
            identificacion=identificacion,
            telefono=telefono,
            correo=correo,
            direccion=None,
            papeles=papeles,
            cuenta_bancaria=None,
            total_inmuebles=total_inmuebles,
        )
        self.items[person_id] = persona
        return persona

    async def listar(
        self, filtros: PersonaFiltros, *, limit: int, offset: int
    ) -> tuple[list[Persona], int]:
        items = sorted(self.items.values(), key=lambda p: p.id, reverse=True)
        if filtros.solo_con_papel:
            items = [p for p in items if p.papeles]
        if filtros.papel:
            items = [p for p in items if filtros.papel in p.papeles]
        if filtros.q:
            q = filtros.q.lower()
            items = [p for p in items if q in p.nombre.lower() or q in (p.identificacion or "")]
        if filtros.correo:
            items = [p for p in items if filtros.correo.lower() in (p.correo or "")]
        if filtros.contrato_id is not None:
            ids = self.codeudores_por_contrato.get(filtros.contrato_id, set())
            items = [p for p in items if p.id in ids]
        return items[offset : offset + limit], len(items)

    async def obtener(self, person_id: int) -> Persona | None:
        return self.items.get(person_id)

    async def buscar_por_identificacion(self, tipo: str, numero: str) -> Persona | None:
        return next(
            (
                p
                for p in self.items.values()
                if (p.tipo_identificacion, p.identificacion) == (tipo, numero)
            ),
            None,
        )

    async def crear(self, datos: PersonaCreate, papeles: list[Papel]) -> Persona:
        self._exigir_identificacion_libre(datos, excepto=None)
        person_id = len(self.items) + 1
        persona = self._desde(person_id, datos, papeles)
        self.items[person_id] = persona
        return persona

    async def actualizar(
        self, person_id: int, datos: PersonaCreate, papeles: list[Papel]
    ) -> Persona | None:
        if person_id not in self.items:
            return None
        self._exigir_identificacion_libre(datos, excepto=person_id)
        persona = self._desde(person_id, datos, papeles)
        self.items[person_id] = persona
        return persona

    async def contar_dependencias(self, person_id: int) -> Dependencias:
        return self.dependencias.get(person_id, Dependencias())

    async def eliminar(self, person_id: int) -> bool:
        return self.items.pop(person_id, None) is not None

    async def detalle(self, person_id: int) -> PersonaDetalle | None:
        persona = self.items.get(person_id)
        if persona is None:
            return None
        contratos = self.contratos.get(person_id, {})
        return PersonaDetalle(
            **persona.model_dump(),
            inmuebles=self.inmuebles.get(person_id, []),
            contratos_como_propietario=contratos.get("propietario", []),
            contratos_como_arrendatario=contratos.get("arrendatario", []),
            contratos_como_codeudor=contratos.get("codeudor", []),
            usuario=self.usuarios.get(person_id),
        )

    def _exigir_identificacion_libre(self, datos: PersonaCreate, excepto: int | None) -> None:
        for persona in self.items.values():
            if persona.id == excepto:
                continue
            if (persona.tipo_identificacion, persona.identificacion) == (
                datos.tipo_identificacion,
                datos.identificacion,
            ):
                raise IdentificacionDuplicadaError()

    def _desde(self, person_id: int, datos: PersonaCreate, papeles: list[Papel]) -> Persona:
        cuenta = datos.cuenta_bancaria
        return Persona(
            id=person_id,
            nombre=datos.nombre,
            tipo_identificacion=datos.tipo_identificacion,
            identificacion=datos.identificacion,
            telefono=datos.telefono,
            correo=datos.correo,
            direccion=datos.direccion,
            papeles=papeles,
            cuenta_bancaria=None
            if cuenta is None
            else CuentaBancaria(id=person_id, **cuenta.model_dump()),
            total_inmuebles=self.items[person_id].total_inmuebles if person_id in self.items else 0,
        )


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


class InMemoryAuthRepository:
    def __init__(self) -> None:
        self.cuentas: dict[str, CuentaLogin] = {}

    def agregar(
        self,
        user_name: str,
        clave: str,
        *,
        roles: tuple[Role, ...] = (Role.ADMIN_SISTEMAS,),
        is_active: bool = True,
        locked_until: datetime | None = None,
        attempts: int = 0,
    ) -> CuentaLogin:
        cuenta = CuentaLogin(
            account_id=len(self.cuentas) + 1,
            nombre=f"Persona {user_name}",
            hashed_password=hash_password(clave, iterations=ITERACIONES_PRUEBA),
            is_active=is_active,
            failed_login_attempts=attempts,
            locked_until=locked_until,
            roles=list(roles),
        )
        self.cuentas[user_name] = cuenta
        return cuenta

    def por_id(self, account_id: int) -> CuentaLogin:
        return next(c for c in self.cuentas.values() if c.account_id == account_id)

    def _set(self, cuenta: CuentaLogin) -> None:
        name = next(n for n, c in self.cuentas.items() if c.account_id == cuenta.account_id)
        self.cuentas[name] = cuenta

    async def find_for_login(self, user_name: str) -> CuentaLogin | None:
        return self.cuentas.get(user_name)

    async def register_failed_attempt(
        self, account_id: int, *, max_attempts: int, lock_minutes: int, now: datetime
    ) -> tuple[int, datetime | None]:
        cuenta = self.por_id(account_id)
        previous = cuenta.locked_until
        attempts = 1 if previous and previous <= now else cuenta.failed_login_attempts + 1
        locked = now + timedelta(minutes=lock_minutes) if attempts >= max_attempts else None
        self._set(replace(cuenta, failed_login_attempts=attempts, locked_until=locked))
        return attempts, locked

    async def reset_attempts(self, account_id: int) -> None:
        self._set(replace(self.por_id(account_id), failed_login_attempts=0, locked_until=None))


class InMemoryUsuariosRepository:
    def __init__(self) -> None:
        self.items: dict[int, Usuario] = {}
        self.hashes: dict[int, str] = {}

    def agregar(
        self, usuario: str, rol: Role, *, activo: bool = True, bloqueada: bool = False
    ) -> Usuario:
        account_id = len(self.items) + 1
        now = datetime.now(UTC)
        item = Usuario(
            id=account_id,
            usuario=usuario,
            nombre=f"Persona {usuario}",
            tipo_identificacion="CC",
            identificacion=f"10000{account_id}",
            correo=f"{usuario}@example.test",
            rol=rol,
            activo=activo,
            bloqueada=bloqueada,
            bloqueada_hasta=now + timedelta(minutes=15) if bloqueada else None,
            intentos_fallidos=3 if bloqueada else 0,
            creado_en=now,
        )
        self.items[account_id] = item
        self.hashes[account_id] = "hash-previo"
        return item

    async def listar(
        self,
        *,
        q: str | None,
        rol: Role | None,
        estado: EstadoUsuario | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Usuario], int]:
        items = sorted(self.items.values(), key=lambda u: u.usuario)
        if q:
            items = [u for u in items if q.lower() in u.usuario or q.lower() in u.nombre.lower()]
        if rol:
            items = [u for u in items if u.rol == rol]
        if estado == "activo":
            items = [u for u in items if u.activo and not u.bloqueada]
        elif estado == "inactivo":
            items = [u for u in items if not u.activo]
        elif estado == "bloqueado":
            items = [u for u in items if u.bloqueada]
        return items[offset : offset + limit], len(items)

    async def obtener(self, account_id: int) -> Usuario | None:
        return self.items.get(account_id)

    async def crear(self, datos: UsuarioCreate, hashed_password: str) -> Usuario:
        if any(u.usuario == datos.usuario for u in self.items.values()):
            raise UsuarioDuplicadoError()
        account_id = len(self.items) + 1
        item = Usuario(
            id=account_id,
            usuario=datos.usuario,
            nombre=datos.nombre,
            tipo_identificacion=datos.tipo_identificacion,
            identificacion=datos.identificacion,
            correo=datos.correo,
            rol=datos.rol,
            activo=datos.activo,
            bloqueada=False,
            bloqueada_hasta=None,
            intentos_fallidos=0,
            creado_en=datetime.now(UTC),
        )
        self.items[account_id] = item
        self.hashes[account_id] = hashed_password
        return item

    async def actualizar(
        self, account_id: int, datos: UsuarioUpdate, hashed_password: str | None
    ) -> Usuario | None:
        actual = self.items.get(account_id)
        if actual is None:
            return None
        item = actual.model_copy(
            update={
                "nombre": datos.nombre,
                "tipo_identificacion": datos.tipo_identificacion,
                "identificacion": datos.identificacion,
                "correo": datos.correo,
                "rol": datos.rol,
                "activo": datos.activo,
            }
        )
        self.items[account_id] = item
        if hashed_password is not None:
            self.hashes[account_id] = hashed_password
        return item

    async def eliminar(self, account_id: int) -> bool:
        return self.items.pop(account_id, None) is not None

    async def count_other_active_admins(self, account_id: int) -> int:
        return sum(
            1
            for u in self.items.values()
            if u.id != account_id and u.activo and u.rol == Role.ADMIN_SISTEMAS
        )

    async def unlock(self, account_id: int) -> Usuario | None:
        actual = self.items.get(account_id)
        if actual is None:
            return None
        item = actual.model_copy(
            update={"bloqueada": False, "bloqueada_hasta": None, "intentos_fallidos": 0}
        )
        self.items[account_id] = item
        return item


RESUMEN_DE_PRUEBA = Resumen(
    personas=ResumenPersonas(total=6, propietarios=2, arrendatarios=2, codeudores=3),
    inmuebles=ResumenInmuebles(total=3, ocupados=1, disponibles=1),
    contratos=ResumenContratos(
        total=2,
        vigentes=2,
        por_vencer_30=0,
        por_vencer_60=1,
        finalizados=0,
        codeudores_vinculados=3,
    ),
    usuarios=ResumenUsuarios(total=3, activos=3, bloqueados=0),
)


class InMemoryResumenRepository:
    async def obtener(self) -> Resumen:
        return RESUMEN_DE_PRUEBA
