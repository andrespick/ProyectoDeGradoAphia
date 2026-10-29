"""Funciones del Administrador de Sistemas: usuarios (clave temporal y sesiones), configuración,
auditoría, estado del sistema, respaldos y catálogos."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
import pytest

from core.errors import DatabaseUnavailableError
from modules.auditoria.service import Auditor
from modules.auth.passwords import verify_password
from modules.auth.schemas import Principal, Role
from tests.conftest import bearer
from tests.fakes import (
    InMemoryAuditoriaRepository,
    InMemoryCatalogosAdminRepository,
    InMemoryConfiguracionRepository,
    InMemorySistemaRepository,
    InMemoryUsuariosRepository,
)

pytestmark = pytest.mark.anyio

ASESOR = bearer(roles=(Role.ASESOR,))
ADMIN = bearer(sujeto="1")


class TestUsuarios:
    async def test_restablecer_clave_entrega_clave_temporal_y_cierra_sesiones(
        self,
        client: httpx.AsyncClient,
        usuarios_repository: InMemoryUsuariosRepository,
        auditoria_repository: InMemoryAuditoriaRepository,
    ) -> None:
        usuario = usuarios_repository.agregar("asesor1", Role.ASESOR, bloqueada=True)

        response = await client.post(f"/api/v1/usuarios/{usuario.id}/restablecer-clave")

        assert response.status_code == 200
        clave = response.json()["clave_temporal"]
        assert len(clave) >= 12
        assert any(c.isdigit() for c in clave) and any(c.isalpha() for c in clave)
        assert verify_password(clave, usuarios_repository.hashes[usuario.id])
        assert usuarios_repository.sesiones_cerradas == [usuario.id]
        assert usuarios_repository.items[usuario.id].debe_cambiar_clave is True
        assert usuarios_repository.items[usuario.id].bloqueada is False
        assert ("restablecer_clave", "usuario", usuario.id) in auditoria_repository.acciones()

    async def test_cerrar_sesiones(
        self, client: httpx.AsyncClient, usuarios_repository: InMemoryUsuariosRepository
    ) -> None:
        usuario = usuarios_repository.agregar("asesor1", Role.ASESOR)

        response = await client.post(f"/api/v1/usuarios/{usuario.id}/cerrar-sesiones")
        inexistente = await client.post("/api/v1/usuarios/99/cerrar-sesiones")

        assert response.status_code == 204
        assert usuarios_repository.sesiones_cerradas == [usuario.id]
        assert inexistente.status_code == 404

    @pytest.mark.parametrize("accion", ["restablecer-clave", "cerrar-sesiones"])
    async def test_no_aplica_sobre_la_cuenta_propia(
        self,
        db_client: httpx.AsyncClient,
        usuarios_repository: InMemoryUsuariosRepository,
        accion: str,
    ) -> None:
        usuarios_repository.agregar("admin", Role.ADMIN_SISTEMAS)

        response = await db_client.post(f"/api/v1/usuarios/1/{accion}", headers=ADMIN)

        assert response.status_code == 409
        assert response.json()["error"]["codigo"] == "usuario_actual"

    async def test_la_clave_propia_no_se_cambia_desde_editar(
        self, db_client: httpx.AsyncClient, usuarios_repository: InMemoryUsuariosRepository
    ) -> None:
        admin = usuarios_repository.agregar("admin", Role.ADMIN_SISTEMAS)
        datos = {
            "nombre": admin.nombre,
            "tipo_identificacion": "CC",
            "identificacion": admin.identificacion,
            "correo": admin.correo,
            "rol": "admin_sistemas",
            "activo": True,
        }

        con_clave = await db_client.put(
            "/api/v1/usuarios/1", json={**datos, "clave": "Nueva.Clave22"}, headers=ADMIN
        )
        sin_clave = await db_client.put("/api/v1/usuarios/1", json=datos, headers=ADMIN)

        assert con_clave.status_code == 409
        assert "Cambiar contraseña" in con_clave.json()["error"]["mensaje"]
        assert sin_clave.status_code == 200
        assert usuarios_repository.sesiones_cerradas == []

    async def test_cambiar_rol_o_clave_cierra_sus_sesiones(
        self, client: httpx.AsyncClient, usuarios_repository: InMemoryUsuariosRepository
    ) -> None:
        usuario = usuarios_repository.agregar("asesor1", Role.ASESOR)
        base = {
            "nombre": usuario.nombre,
            "tipo_identificacion": "CC",
            "identificacion": usuario.identificacion,
            "correo": usuario.correo,
            "activo": True,
        }

        igual = await client.put(f"/api/v1/usuarios/{usuario.id}", json={**base, "rol": "asesor"})
        assert igual.status_code == 200
        assert usuarios_repository.sesiones_cerradas == []

        await client.put(f"/api/v1/usuarios/{usuario.id}", json={**base, "rol": "administrativo"})
        assert usuarios_repository.sesiones_cerradas == [usuario.id]

    async def test_la_clave_respeta_el_largo_de_la_politica(
        self,
        client: httpx.AsyncClient,
        configuracion_repository: InMemoryConfiguracionRepository,
    ) -> None:
        configuracion_repository.politica = configuracion_repository.politica.model_copy(
            update={"largo_minimo_clave": 14}
        )

        response = await client.post(
            "/api/v1/usuarios",
            json={
                "usuario": "mperez",
                "nombre": "María Pérez",
                "tipo_identificacion": "CC",
                "identificacion": "1020304050",
                "correo": "maria@example.test",
                "clave": "Clave.Segura1",
                "rol": "asesor",
            },
        )

        assert response.status_code == 422
        error = response.json()["error"]
        assert error["codigo"] == "clave_insegura"
        assert error["detalles"][0]["campo"] == "clave"
        assert "14 caracteres" in error["mensaje"]


class TestConfiguracion:
    async def test_politica_se_lee_y_se_guarda(
        self, client: httpx.AsyncClient, auditoria_repository: InMemoryAuditoriaRepository
    ) -> None:
        nueva = {
            "max_intentos": 5,
            "minutos_bloqueo": 30,
            "horas_sesion": 4,
            "largo_minimo_clave": 10,
        }

        guardada = await client.put("/api/v1/configuracion/seguridad", json=nueva)
        leida = await client.get("/api/v1/configuracion/seguridad")

        assert guardada.status_code == 200
        assert leida.json() == nueva
        assert auditoria_repository.eventos[-1].entidad == "politica_seguridad"

    @pytest.mark.parametrize(
        "cambio",
        [
            {"max_intentos": 2},
            {"max_intentos": 11},
            {"minutos_bloqueo": 4},
            {"horas_sesion": 25},
            {"largo_minimo_clave": 7},
            {"extra": 1},
        ],
    )
    async def test_politica_fuera_de_limites_responde_422(
        self, client: httpx.AsyncClient, cambio: dict[str, int]
    ) -> None:
        base = {
            "max_intentos": 3,
            "minutos_bloqueo": 15,
            "horas_sesion": 8,
            "largo_minimo_clave": 8,
        }

        response = await client.put("/api/v1/configuracion/seguridad", json={**base, **cambio})

        assert response.status_code == 422

    async def test_empresa_la_leen_todos_y_solo_el_admin_la_cambia(
        self, db_client: httpx.AsyncClient
    ) -> None:
        datos = {
            "nombre": "  Inmobiliaria   Ficticia S.A.S. ",
            "nit": "900.123.456-7",
            "direccion": "Calle 100 # 10-20",
            "ciudad": "Bogotá",
            "telefono": "601 555 0000",
            "correo": "Contacto@Example.test",
        }

        leida = await db_client.get("/api/v1/configuracion/empresa", headers=ASESOR)
        negada = await db_client.put("/api/v1/configuracion/empresa", json=datos, headers=ASESOR)
        guardada = await db_client.put("/api/v1/configuracion/empresa", json=datos, headers=ADMIN)

        assert leida.status_code == 200
        assert leida.json()["nombre"] == "APHIA S.A.S."
        assert negada.status_code == 403
        assert guardada.status_code == 200
        assert guardada.json()["nombre"] == "Inmobiliaria Ficticia S.A.S."
        assert guardada.json()["correo"] == "contacto@example.test"

    @pytest.mark.parametrize(
        "cambio", [{"nit": "NIT 900"}, {"correo": "no-es-correo"}, {"nombre": ""}, {"logo": "x"}]
    )
    async def test_empresa_invalida_responde_422(
        self, client: httpx.AsyncClient, cambio: dict[str, str]
    ) -> None:
        response = await client.put(
            "/api/v1/configuracion/empresa", json={"nombre": "Empresa", **cambio}
        )

        assert response.status_code == 422

    async def test_politica_negada_a_roles_de_negocio(self, db_client: httpx.AsyncClient) -> None:
        response = await db_client.get("/api/v1/configuracion/seguridad", headers=ASESOR)

        assert response.status_code == 403


class TestAuditoria:
    async def test_lista_los_cambios_con_su_actor_y_filtra(self, client: httpx.AsyncClient) -> None:
        await client.post("/api/v1/sistema/respaldos")
        await client.put(
            "/api/v1/configuracion/seguridad",
            json={
                "max_intentos": 3,
                "minutos_bloqueo": 15,
                "horas_sesion": 8,
                "largo_minimo_clave": 8,
            },
        )

        todos = await client.get("/api/v1/auditoria")
        filtrados = await client.get("/api/v1/auditoria", params={"accion": "solicitar_respaldo"})

        assert todos.json()["total"] == 2
        evento = todos.json()["items"][0]
        assert evento["accion"] == "actualizar"
        assert evento["actor_nombre"] == "Usuario de desarrollo"
        assert evento["actor_id"] is None  # el usuario ficticio no tiene cuenta
        assert [e["accion"] for e in filtrados.json()["items"]] == ["solicitar_respaldo"]

    async def test_solo_el_administrador(self, db_client: httpx.AsyncClient) -> None:
        response = await db_client.get("/api/v1/auditoria", headers=ASESOR)

        assert response.status_code == 403

    async def test_un_fallo_al_auditar_no_rompe_la_operacion(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        class Caida:
            async def registrar(self, evento: object) -> None:
                raise DatabaseUnavailableError()

        actor = Principal(sujeto="7", nombre="Ana", roles=[Role.ASESOR], modo="database")

        await Auditor(Caida(), actor).registrar("crear", "persona", 1)  # type: ignore[arg-type]

        assert '"event": "auditoria_no_registrada"' in capsys.readouterr().out


class TestSistema:
    async def test_estado_completo(
        self, client: httpx.AsyncClient, sistema_repository: InMemorySistemaRepository
    ) -> None:
        sistema_repository.respaldo("ok", datetime.now(UTC) - timedelta(hours=2))

        body = (await client.get("/api/v1/sistema/estado")).json()

        assert body["api"]["entorno"] == "test"
        assert body["base_de_datos"]["disponible"] is True
        assert body["migraciones"]["ultima"] == "0018"
        assert body["registros"]["en_papelera"] == 1
        assert body["respaldos"]["atrasado"] is False
        assert body["respaldos"]["ultimo_exitoso"]["estado"] == "ok"

    @pytest.mark.parametrize("horas", [None, 30])
    async def test_respaldo_atrasado(
        self,
        client: httpx.AsyncClient,
        sistema_repository: InMemorySistemaRepository,
        horas: int | None,
    ) -> None:
        if horas is not None:
            sistema_repository.respaldo("ok", datetime.now(UTC) - timedelta(hours=horas))

        body = (await client.get("/api/v1/sistema/estado")).json()

        assert body["respaldos"]["atrasado"] is True

    async def test_sin_base_de_datos_el_panel_responde(
        self, client: httpx.AsyncClient, sistema_repository: InMemorySistemaRepository
    ) -> None:
        sistema_repository.disponible = False

        response = await client.get("/api/v1/sistema/estado")

        assert response.status_code == 200
        assert response.json()["base_de_datos"] == {
            "disponible": False,
            "latencia_ms": None,
            "version": None,
            "tamano_bytes": None,
        }
        assert response.json()["respaldos"] is None

    async def test_solicitar_respaldo_una_vez(
        self, client: httpx.AsyncClient, auditoria_repository: InMemoryAuditoriaRepository
    ) -> None:
        primera = await client.post("/api/v1/sistema/respaldos")
        segunda = await client.post("/api/v1/sistema/respaldos")
        lista = await client.get("/api/v1/sistema/respaldos")

        assert primera.status_code == 202
        assert primera.json()["estado"] == "solicitado"
        assert primera.json()["origen"] == "manual"
        assert segunda.status_code == 409
        assert segunda.json()["error"]["codigo"] == "respaldo_en_curso"
        assert lista.json()["total"] == 1
        assert auditoria_repository.acciones() == [("solicitar_respaldo", "respaldo", 1)]

    async def test_solo_el_administrador(self, db_client: httpx.AsyncClient) -> None:
        assert (await db_client.get("/api/v1/sistema/estado", headers=ASESOR)).status_code == 403
        assert (
            await db_client.post("/api/v1/sistema/respaldos", headers=ASESOR)
        ).status_code == 403


class TestCatalogos:
    async def test_crear_renombrar_y_eliminar(
        self,
        client: httpx.AsyncClient,
        catalogos_admin_repository: InMemoryCatalogosAdminRepository,
        auditoria_repository: InMemoryAuditoriaRepository,
    ) -> None:
        creado = await client.post(
            "/api/v1/catalogos/tipos-identificacion",
            json={"codigo": "rc", "nombre": "Registro civil"},
        )
        item_id = creado.json()["id"]
        renombrado = await client.put(
            f"/api/v1/catalogos/tipos-identificacion/{item_id}",
            json={"nombre": "Registro  civil de nacimiento"},
        )
        eliminado = await client.delete(f"/api/v1/catalogos/tipos-identificacion/{item_id}")
        lista = await client.get("/api/v1/catalogos/tipos-identificacion")

        assert creado.status_code == 201
        assert creado.json()["codigo"] == "RC"
        assert renombrado.json()["nombre"] == "Registro civil de nacimiento"
        assert eliminado.status_code == 204
        assert [i["codigo"] for i in lista.json()] == ["CC"]
        assert [a for a, _, _ in auditoria_repository.acciones()] == [
            "crear",
            "actualizar",
            "eliminar",
        ]

    async def test_reglas(self, client: httpx.AsyncClient) -> None:
        sin_codigo = await client.post(
            "/api/v1/catalogos/tipos-contrato", json={"nombre": "Comodato"}
        )
        ciudad = await client.post("/api/v1/catalogos/ciudades", json={"nombre": "Pasto"})
        duplicada = await client.post("/api/v1/catalogos/ciudades", json={"nombre": "Bogotá"})
        en_uso = await client.delete("/api/v1/catalogos/tipos-identificacion/1")
        desconocido = await client.get("/api/v1/catalogos/roles")
        inexistente = await client.put("/api/v1/catalogos/ciudades/5", json={"nombre": "X"})

        assert sin_codigo.status_code == 422
        assert sin_codigo.json()["error"]["detalles"][0]["campo"] == "codigo"
        assert ciudad.status_code == 201 and ciudad.json()["codigo"] is None
        assert duplicada.status_code == 409
        assert en_uso.status_code == 409
        assert en_uso.json()["error"]["codigo"] == "catalogo_en_uso"
        assert "4 registro(s)" in en_uso.json()["error"]["mensaje"]
        assert desconocido.status_code == 422
        assert inexistente.status_code == 404

    async def test_solo_el_administrador_los_modifica(self, db_client: httpx.AsyncClient) -> None:
        lectura = await db_client.get("/api/v1/catalogos", headers=ASESOR)
        lista = await db_client.get("/api/v1/catalogos/ciudades", headers=ASESOR)
        crear = await db_client.post(
            "/api/v1/catalogos/ciudades", json={"nombre": "Pasto"}, headers=ASESOR
        )

        assert lectura.status_code == 200
        assert lista.status_code == 403
        assert crear.status_code == 403
