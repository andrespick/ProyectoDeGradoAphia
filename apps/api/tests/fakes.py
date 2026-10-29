"""Repositorios en memoria para pruebas unitarias (sin MySQL)."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from typing import Any

from core.errors import CatalogoInvalidoError, IdentificacionDuplicadaError
from modules.auditoria.schemas import AuditoriaFiltros, EventoAuditoria, NuevoEvento
from modules.auth.passwords import hash_password
from modules.auth.repository import CuentaLogin, EstadoSesion
from modules.auth.schemas import Role
from modules.buscar.schemas import ResultadosBusqueda
from modules.catalogos.repository import (
    CatalogoDuplicadoError,
    CatalogoEnUsoError,
    ItemCatalogoNoEncontradoError,
)
from modules.catalogos.schemas import (
    CatalogoAdministrable,
    Catalogos,
    Ciudad,
    ItemCatalogo,
    ItemCatalogoCreate,
    Opcion,
)
from modules.configuracion.schemas import POLITICA_INICIAL, Empresa, PoliticaSeguridad
from modules.contratos.schemas import (
    DIAS_POR_VENCER,
    Contrato,
    ContratoCreate,
    ContratoFiltros,
    estado_de,
)
from modules.inmuebles.schemas import Inmueble, InmuebleCreate, InmuebleFiltros, ServicioPublico
from modules.papelera.schemas import EntradaPapelera, RegistroEliminado, TipoRegistro
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
    PersonaResumen,
)
from modules.personas.service import PersonaNoEncontradaError
from modules.resumen.schemas import (
    Resumen,
    ResumenContratos,
    ResumenInmuebles,
    ResumenPersonas,
    ResumenUsuarios,
)
from modules.sistema.schemas import (
    ConteoRegistros,
    Diagnostico,
    EstadoBaseDatos,
    EstadoMigraciones,
    Respaldo,
)
from modules.usuarios.repository import UsuarioDuplicadoError
from modules.usuarios.schemas import EstadoUsuario, Usuario, UsuarioCreate, UsuarioUpdate

# Pocas iteraciones para que las pruebas sean rápidas; el formato es el mismo.
ITERACIONES_PRUEBA = 1_000


class InMemoryPapeleraRepository:
    """Compartida por los fakes de personas, inmuebles y contratos (como la tabla real)."""

    def __init__(self) -> None:
        self.items: dict[int, tuple[RegistroEliminado, dict[str, Any]]] = {}

    def agregar(self, entrada: EntradaPapelera) -> None:
        record_id = max(self.items, default=0) + 1
        registro = RegistroEliminado(
            id=record_id,
            tipo=entrada.tipo,
            entidad_id=entrada.entidad_id,
            descripcion=entrada.descripcion,
            eliminado_en=datetime.now(UTC),
            eliminado_por=entrada.eliminado_por,
        )
        self.items[record_id] = (registro, entrada.datos)

    async def listar(
        self, tipo: TipoRegistro | None, *, limit: int, offset: int
    ) -> tuple[list[RegistroEliminado], int]:
        items = [r for r, _ in sorted(self.items.values(), key=lambda x: -x[0].id)]
        if tipo:
            items = [r for r in items if r.tipo == tipo]
        return items[offset : offset + limit], len(items)

    async def obtener(self, record_id: int) -> tuple[RegistroEliminado, dict[str, Any]] | None:
        return self.items.get(record_id)

    async def eliminar(self, record_id: int) -> bool:
        return self.items.pop(record_id, None) is not None


class InMemoryPersonasRepository:
    def __init__(self, papelera: InMemoryPapeleraRepository | None = None) -> None:
        self.papelera = papelera or InMemoryPapeleraRepository()
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
        person_id = max(self.items, default=0) + 1
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

    async def eliminar(self, person_id: int, papelera: EntradaPapelera) -> bool:
        if self.items.pop(person_id, None) is None:
            return False
        self.papelera.agregar(papelera)
        return True

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
        debe_cambiar_clave: bool = False,
    ) -> CuentaLogin:
        cuenta = CuentaLogin(
            account_id=len(self.cuentas) + 1,
            nombre=f"Persona {user_name}",
            hashed_password=hash_password(clave, iterations=ITERACIONES_PRUEBA),
            is_active=is_active,
            failed_login_attempts=attempts,
            locked_until=locked_until,
            roles=list(roles),
            debe_cambiar_clave=debe_cambiar_clave,
        )
        self.cuentas[user_name] = cuenta
        return cuenta

    def por_id(self, account_id: int) -> CuentaLogin:
        return next(c for c in self.cuentas.values() if c.account_id == account_id)

    async def find_by_id(self, account_id: int) -> CuentaLogin | None:
        return next((c for c in self.cuentas.values() if c.account_id == account_id), None)

    async def estado_sesion(self, account_id: int) -> EstadoSesion | None:
        cuenta = await self.find_by_id(account_id)
        if cuenta is None:
            # Los tokens de ``bearer()`` no tienen cuenta en el fake: se tratan como sesiones
            # vigentes (v0) para que cada prueba no tenga que registrar su usuario.
            return EstadoSesion(activa=True, version=0, debe_cambiar_clave=False)
        return EstadoSesion(
            activa=cuenta.is_active,
            version=cuenta.session_version,
            debe_cambiar_clave=cuenta.debe_cambiar_clave,
        )

    async def cambiar_clave(self, account_id: int, hashed_password: str) -> int:
        cuenta = self.por_id(account_id)
        version = cuenta.session_version + 1
        self._set(
            replace(
                cuenta,
                hashed_password=hashed_password,
                debe_cambiar_clave=False,
                session_version=version,
            )
        )
        return version

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
        self.sesiones_cerradas: list[int] = []

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

    async def restablecer_clave(self, account_id: int, hashed_password: str) -> Usuario | None:
        if await self.unlock(account_id) is None:
            return None
        self.hashes[account_id] = hashed_password
        self.sesiones_cerradas.append(account_id)
        item = self.items[account_id].model_copy(update={"debe_cambiar_clave": True})
        self.items[account_id] = item
        return item

    async def cerrar_sesiones(self, account_id: int) -> bool:
        if account_id not in self.items:
            return False
        self.sesiones_cerradas.append(account_id)
        return True


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


class InMemoryInmueblesRepository:
    def __init__(self, papelera: InMemoryPapeleraRepository | None = None) -> None:
        self.papelera = papelera or InMemoryPapeleraRepository()
        self.items: dict[int, Inmueble] = {}
        self.personas: dict[int, PersonaResumen] = {}
        self.contratos: dict[int, int] = {}
        self.papeles_agregados: list[tuple[int, str]] = []

    def persona(self, person_id: int, nombre: str) -> PersonaResumen:
        resumen = PersonaResumen(
            id=person_id,
            nombre=nombre,
            tipo_identificacion="CC",
            identificacion=f"100{person_id}",
            telefono=None,
            correo=None,
        )
        self.personas[person_id] = resumen
        return resumen

    async def listar(
        self, filtros: InmuebleFiltros, *, limit: int, offset: int
    ) -> tuple[list[Inmueble], int]:
        items = sorted(self.items.values(), key=lambda i: i.id, reverse=True)
        if filtros.estado:
            items = [i for i in items if i.estado == filtros.estado.upper()]
        if filtros.ciudad:
            items = [i for i in items if filtros.ciudad.lower() in (i.ciudad or "").lower()]
        if filtros.propietario_id is not None:
            items = [
                i for i in items if any(p.id == filtros.propietario_id for p in i.propietarios)
            ]
        if filtros.q:
            q = filtros.q.lower()
            items = [
                i for i in items if q in i.direccion.lower() or q in (i.matricula or "").lower()
            ]
        return items[offset : offset + limit], len(items)

    async def obtener(self, property_id: int) -> Inmueble | None:
        return self.items.get(property_id)

    async def crear(self, datos: InmuebleCreate) -> Inmueble:
        property_id = max(self.items, default=0) + 1
        self.items[property_id] = self._desde(property_id, datos)
        return self.items[property_id]

    async def actualizar(self, property_id: int, datos: InmuebleCreate) -> Inmueble | None:
        if property_id not in self.items:
            return None
        self.items[property_id] = self._desde(property_id, datos)
        return self.items[property_id]

    async def contar_contratos(self, property_id: int) -> int:
        return self.contratos.get(property_id, 0)

    async def eliminar(self, property_id: int, papelera: EntradaPapelera) -> bool:
        if self.items.pop(property_id, None) is None:
            return False
        self.papelera.agregar(papelera)
        return True

    def _desde(self, property_id: int, datos: InmuebleCreate) -> Inmueble:
        if datos.estado and datos.estado not in {"DISPONIBLE", "OCUPADO"}:
            raise CatalogoInvalidoError("estado")
        propietarios = []
        for person_id in datos.propietarios_ids:
            if person_id not in self.personas:
                raise PersonaNoEncontradaError(f"La persona {person_id} no existe.")
            propietarios.append(self.personas[person_id])
            self.papeles_agregados.append((person_id, "propietario"))
        return Inmueble(
            id=property_id,
            direccion=datos.direccion,
            ciudad=datos.ciudad,
            matricula=datos.matricula,
            canon=datos.canon,
            moneda="COP" if datos.canon is not None else None,
            estado=datos.estado,
            servicios=[
                ServicioPublico(id=n, **s.model_dump()) for n, s in enumerate(datos.servicios, 1)
            ],
            propietarios=propietarios,
            total_contratos=self.contratos.get(property_id, 0),
        )


class InMemoryContratosRepository:
    """Contratos en memoria; `hoy` fijo para que estado y días restantes sean deterministas."""

    def __init__(self, papelera: InMemoryPapeleraRepository | None = None) -> None:
        self.papelera = papelera or InMemoryPapeleraRepository()
        self.items: dict[int, Contrato] = {}
        self.personas: dict[int, PersonaResumen] = {}
        self.inmuebles: dict[int, tuple[InmuebleResumen, list[int]]] = {}
        self.dependencias: dict[int, tuple[int, int]] = {}
        self.papeles_agregados: list[tuple[int, str]] = []
        self.hoy = date(2026, 10, 28)

    def persona(self, person_id: int, nombre: str) -> PersonaResumen:
        resumen = PersonaResumen(
            id=person_id,
            nombre=nombre,
            tipo_identificacion="CC",
            identificacion=f"100{person_id}",
            telefono=None,
            correo=None,
        )
        self.personas[person_id] = resumen
        return resumen

    def inmueble(self, property_id: int, direccion: str, duenos: list[int]) -> InmuebleResumen:
        resumen = InmuebleResumen(id=property_id, direccion=direccion, ciudad="Bogotá", estado=None)
        self.inmuebles[property_id] = (resumen, duenos)
        return resumen

    async def listar(
        self, filtros: ContratoFiltros, *, limit: int, offset: int
    ) -> tuple[list[Contrato], int]:
        items = sorted(self.items.values(), key=lambda c: (c.fecha_inicio, c.id), reverse=True)
        if filtros.fecha_desde:
            items = [c for c in items if c.fecha_fin is None or c.fecha_fin >= filtros.fecha_desde]
        if filtros.fecha_hasta:
            items = [c for c in items if c.fecha_inicio <= filtros.fecha_hasta]
        if filtros.inmueble_id is not None:
            items = [c for c in items if c.inmueble.id == filtros.inmueble_id]
        if filtros.propietario_id is not None:
            items = [
                c for c in items if any(p.id == filtros.propietario_id for p in c.propietarios)
            ]
        if filtros.inquilino_id is not None:
            items = [
                c for c in items if c.arrendatario and c.arrendatario.id == filtros.inquilino_id
            ]
        if filtros.tipo:
            items = [c for c in items if c.tipo == filtros.tipo.upper()]
        if filtros.estado == "por_vencer":
            items = [
                c
                for c in items
                if c.fecha_fin is not None and 0 <= (c.fecha_fin - self.hoy).days <= DIAS_POR_VENCER
            ]
        elif filtros.estado:
            items = [c for c in items if c.estado == filtros.estado]
        if filtros.q:
            q = filtros.q.lower()
            items = [
                c
                for c in items
                if q in c.inmueble.direccion.lower()
                or any(q in p.nombre.lower() for p in self._partes(c))
            ]
        return items[offset : offset + limit], len(items)

    async def obtener(self, agreement_id: int) -> Contrato | None:
        return self.items.get(agreement_id)

    async def propietarios_del_inmueble(self, property_id: int) -> list[int] | None:
        return None if property_id not in self.inmuebles else list(self.inmuebles[property_id][1])

    async def crear(self, datos: ContratoCreate, propietarios_ids: list[int]) -> Contrato:
        agreement_id = max(self.items, default=0) + 1
        self.items[agreement_id] = self._desde(agreement_id, datos, propietarios_ids)
        return self.items[agreement_id]

    async def actualizar(
        self, agreement_id: int, datos: ContratoCreate, propietarios_ids: list[int]
    ) -> Contrato | None:
        if agreement_id not in self.items:
            return None
        self.items[agreement_id] = self._desde(agreement_id, datos, propietarios_ids)
        return self.items[agreement_id]

    async def contar_dependencias(self, agreement_id: int) -> tuple[int, int]:
        return self.dependencias.get(agreement_id, (0, 0))

    async def eliminar(self, agreement_id: int, papelera: EntradaPapelera) -> bool:
        if self.items.pop(agreement_id, None) is None:
            return False
        self.papelera.agregar(papelera)
        return True

    @staticmethod
    def _partes(contrato: Contrato) -> list[PersonaResumen]:
        return [
            *contrato.propietarios,
            *([contrato.arrendatario] if contrato.arrendatario else []),
            *contrato.codeudores,
        ]

    def _persona(self, person_id: int, papel: str) -> PersonaResumen:
        if person_id not in self.personas:
            raise PersonaNoEncontradaError(f"La persona {person_id} no existe.")
        self.papeles_agregados.append((person_id, papel))
        return self.personas[person_id]

    def _desde(self, agreement_id: int, datos: ContratoCreate, propietarios: list[int]) -> Contrato:
        if datos.tipo not in {"ARRENDAMIENTO", "ADMINISTRACION"}:
            raise CatalogoInvalidoError("tipo")
        estado, dias = estado_de(datos.fecha_inicio, datos.fecha_fin, self.hoy)
        return Contrato(
            id=agreement_id,
            tipo=datos.tipo,
            inmueble=self.inmuebles[datos.inmueble_id][0],
            fecha_inicio=datos.fecha_inicio,
            fecha_fin=datos.fecha_fin,
            canon_pactado=datos.canon_pactado,
            moneda="COP" if datos.canon_pactado is not None else None,
            estado=estado,
            dias_restantes=dias,
            propietarios=[self._persona(p, "propietario") for p in propietarios],
            arrendatario=(
                None
                if datos.arrendatario_id is None
                else self._persona(datos.arrendatario_id, "arrendatario")
            ),
            codeudores=[self._persona(c, "codeudor") for c in datos.codeudores_ids],
            condiciones=datos.condiciones,
            texto=datos.texto,
        )


class InMemoryBuscarRepository:
    def __init__(self) -> None:
        self.consultas: list[str] = []
        self.resultado = ResultadosBusqueda(personas=[], inmuebles=[], contratos=[])

    async def buscar(self, q: str) -> ResultadosBusqueda:
        self.consultas.append(q)
        return self.resultado


class InMemoryAuditoriaRepository:
    def __init__(self) -> None:
        self.eventos: list[NuevoEvento] = []

    def acciones(self) -> list[tuple[str, str | None, int | None]]:
        return [(e.accion, e.entidad, e.entidad_id) for e in self.eventos]

    async def registrar(self, evento: NuevoEvento) -> None:
        self.eventos.append(evento)

    async def listar(
        self, filtros: AuditoriaFiltros, *, limit: int, offset: int
    ) -> tuple[list[EventoAuditoria], int]:
        items = [
            EventoAuditoria(
                id=n,
                fecha=datetime(2026, 10, 28, 12, tzinfo=UTC),
                actor_id=e.actor_id,
                actor_nombre=e.actor_nombre,
                actor_usuario=None,
                accion=e.accion,
                entidad=e.entidad,
                entidad_id=e.entidad_id,
                detalle=e.detalle,
                request_id=e.request_id,
            )
            for n, e in enumerate(self.eventos, 1)
        ][::-1]
        if filtros.accion:
            items = [e for e in items if e.accion == filtros.accion]
        if filtros.entidad:
            items = [e for e in items if e.entidad == filtros.entidad]
        if filtros.q:
            items = [e for e in items if filtros.q.lower() in (e.actor_nombre or "").lower()]
        return items[offset : offset + limit], len(items)


class InMemoryConfiguracionRepository:
    def __init__(self) -> None:
        self.politica = POLITICA_INICIAL
        self.empresa = Empresa(nombre="APHIA S.A.S.")

    async def obtener_politica(self) -> PoliticaSeguridad:
        return self.politica

    async def guardar_politica(self, politica: PoliticaSeguridad) -> PoliticaSeguridad:
        self.politica = politica
        return politica

    async def obtener_empresa(self) -> Empresa:
        return self.empresa

    async def guardar_empresa(self, empresa: Empresa) -> Empresa:
        self.empresa = empresa
        return empresa


class InMemorySistemaRepository:
    def __init__(self) -> None:
        self.respaldos: list[Respaldo] = []
        self.disponible = True

    def respaldo(self, estado: str, terminado_en: datetime | None = None) -> Respaldo:
        item = Respaldo(
            id=len(self.respaldos) + 1,
            origen="programado",
            estado=estado,  # type: ignore[arg-type]
            solicitado_en=terminado_en or datetime.now(UTC),
            iniciado_en=terminado_en,
            terminado_en=terminado_en,
            archivo="aphia-20261028T031500Z.tar.age" if estado == "ok" else None,
            tamano_bytes=1024 if estado == "ok" else None,
            copia_externa=False if estado == "ok" else None,
            error=None,
        )
        self.respaldos.append(item)
        return item

    async def diagnostico(self) -> Diagnostico:
        if not self.disponible:
            from core.errors import DatabaseUnavailableError

            raise DatabaseUnavailableError()
        ok = [r for r in self.respaldos if r.estado == "ok"]
        pendientes = [r for r in self.respaldos if r.estado in {"solicitado", "en_curso"}]
        return Diagnostico(
            base_de_datos=EstadoBaseDatos(
                disponible=True, latencia_ms=1.5, version="8.4.0", tamano_bytes=2_097_152
            ),
            migraciones=EstadoMigraciones(
                aplicadas=18, ultima="0018", aplicada_en=datetime(2026, 10, 28, tzinfo=UTC)
            ),
            registros=ConteoRegistros(
                personas=6,
                inmuebles=3,
                contratos=2,
                usuarios=3,
                eventos_auditoria=10,
                en_papelera=1,
            ),
            ultimo_exitoso=ok[-1] if ok else None,
            pendiente=pendientes[0] if pendientes else None,
        )

    async def listar_respaldos(self, *, limit: int, offset: int) -> tuple[list[Respaldo], int]:
        items = self.respaldos[::-1]
        return items[offset : offset + limit], len(items)

    async def solicitar_respaldo(self) -> Respaldo | None:
        if any(r.estado in {"solicitado", "en_curso"} for r in self.respaldos):
            return None
        item = self.respaldo("solicitado").model_copy(update={"origen": "manual"})
        self.respaldos[-1] = item
        return item


class InMemoryCatalogosAdminRepository:
    def __init__(self) -> None:
        self.items: dict[str, dict[int, ItemCatalogo]] = {
            "tipos-identificacion": {
                1: ItemCatalogo(id=1, codigo="CC", nombre="Cédula de ciudadanía", en_uso=4)
            },
            "ciudades": {9001: ItemCatalogo(id=9001, codigo=None, nombre="Bogotá", en_uso=0)},
        }

    async def listar(self, catalogo: CatalogoAdministrable) -> list[ItemCatalogo]:
        return sorted(self.items.get(catalogo, {}).values(), key=lambda i: i.nombre)

    async def crear(
        self, catalogo: CatalogoAdministrable, datos: ItemCatalogoCreate
    ) -> ItemCatalogo:
        items = self.items.setdefault(catalogo, {})
        if any(
            i.nombre == datos.nombre or (datos.codigo and i.codigo == datos.codigo)
            for i in items.values()
        ):
            raise CatalogoDuplicadoError()
        item = ItemCatalogo(
            id=max(items, default=0) + 1, codigo=datos.codigo, nombre=datos.nombre, en_uso=0
        )
        items[item.id] = item
        return item

    async def renombrar(
        self, catalogo: CatalogoAdministrable, item_id: int, nombre: str
    ) -> ItemCatalogo:
        items = self.items.get(catalogo, {})
        if item_id not in items:
            raise ItemCatalogoNoEncontradoError()
        items[item_id] = items[item_id].model_copy(update={"nombre": nombre})
        return items[item_id]

    async def eliminar(self, catalogo: CatalogoAdministrable, item_id: int) -> None:
        items = self.items.get(catalogo, {})
        if item_id not in items:
            raise ItemCatalogoNoEncontradoError()
        if items[item_id].en_uso:
            raise CatalogoEnUsoError(items[item_id].en_uso)
        del items[item_id]
