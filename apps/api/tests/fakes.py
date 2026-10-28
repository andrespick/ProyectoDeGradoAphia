"""Repositorios en memoria para pruebas unitarias (sin MySQL)."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

from modules.auth.passwords import hash_password
from modules.auth.repository import CuentaLogin
from modules.auth.schemas import Role
from modules.catalogos.schemas import Catalogos, Ciudad, Opcion
from modules.clientes.schemas import Cliente
from modules.clientes.service import CorreoDuplicadoError
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
