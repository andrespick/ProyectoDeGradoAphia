"""Sesiones revocables, cambio obligatorio de contraseña y política de seguridad en el login."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from modules.auth.schemas import Role
from modules.configuracion.schemas import PoliticaSeguridad
from tests.fakes import (
    InMemoryAuditoriaRepository,
    InMemoryAuthRepository,
    InMemoryConfiguracionRepository,
)

pytestmark = pytest.mark.anyio

LOGIN = "/api/v1/auth/login"
ME = "/api/v1/auth/me"
CAMBIAR = "/api/v1/auth/cambiar-clave"
CLAVE = "Clave.Segura1"


async def _token(client: httpx.AsyncClient, usuario: str = "ana", clave: str = CLAVE) -> str:
    response = await client.post(LOGIN, json={"usuario": usuario, "clave": clave})
    assert response.status_code == 200, response.text
    return response.json()["token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_cerrar_sesiones_invalida_el_token_al_instante(
    db_client: httpx.AsyncClient, auth_repository: InMemoryAuthRepository
) -> None:
    auth_repository.agregar("ana", CLAVE)
    token = await _token(db_client)
    assert (await db_client.get(ME, headers=_auth(token))).status_code == 200

    cuenta = auth_repository.por_id(1)
    auth_repository._set(replace(cuenta, session_version=cuenta.session_version + 1))
    response = await db_client.get(ME, headers=_auth(token))

    assert response.status_code == 401
    assert response.json()["error"]["mensaje"] == "Su sesión se cerró. Inicie sesión de nuevo."


async def test_desactivar_la_cuenta_corta_la_sesion_abierta(
    db_client: httpx.AsyncClient, auth_repository: InMemoryAuthRepository
) -> None:
    auth_repository.agregar("ana", CLAVE, roles=(Role.ADMINISTRATIVO,))
    token = await _token(db_client)

    auth_repository._set(replace(auth_repository.por_id(1), is_active=False))

    assert (await db_client.get("/api/v1/clientes", headers=_auth(token))).status_code == 401


class TestCambioObligatorio:
    async def test_solo_permite_me_y_cambiar_clave(
        self, db_client: httpx.AsyncClient, auth_repository: InMemoryAuthRepository
    ) -> None:
        auth_repository.agregar("ana", CLAVE, debe_cambiar_clave=True)

        login = await db_client.post(LOGIN, json={"usuario": "ana", "clave": CLAVE})
        token = login.json()["token"]
        usuarios = await db_client.get("/api/v1/usuarios", headers=_auth(token))
        me = await db_client.get(ME, headers=_auth(token))

        assert login.json()["principal"]["debe_cambiar_clave"] is True
        assert usuarios.status_code == 403
        assert usuarios.json()["error"]["codigo"] == "cambio_de_clave_requerido"
        assert me.json()["debe_cambiar_clave"] is True

    async def test_cambiar_clave_entrega_token_nuevo_y_cierra_el_anterior(
        self,
        db_client: httpx.AsyncClient,
        auth_repository: InMemoryAuthRepository,
        auditoria_repository: InMemoryAuditoriaRepository,
    ) -> None:
        auth_repository.agregar("ana", CLAVE, debe_cambiar_clave=True)
        anterior = await _token(db_client)

        response = await db_client.post(
            CAMBIAR,
            json={"clave_actual": CLAVE, "clave_nueva": "Nueva.Clave22"},
            headers=_auth(anterior),
        )

        assert response.status_code == 200
        nuevo = response.json()["token"]
        assert response.json()["principal"]["debe_cambiar_clave"] is False
        assert "Nueva.Clave22" not in response.text
        assert (await db_client.get(ME, headers=_auth(anterior))).status_code == 401
        assert (await db_client.get("/api/v1/usuarios", headers=_auth(nuevo))).status_code == 200
        assert (
            await db_client.post(LOGIN, json={"usuario": "ana", "clave": CLAVE})
        ).status_code == 401
        assert ("cambio_clave", "usuario", 1) in auditoria_repository.acciones()

    @pytest.mark.parametrize(
        ("cuerpo", "campo"),
        [
            ({"clave_actual": "Otra.Clave99", "clave_nueva": "Nueva.Clave22"}, "clave_actual"),
            ({"clave_actual": CLAVE, "clave_nueva": CLAVE}, "clave_nueva"),
            ({"clave_actual": CLAVE, "clave_nueva": "Corta1aa"}, "clave_nueva"),
        ],
        ids=["actual-incorrecta", "igual-a-la-actual", "mas-corta-que-la-politica"],
    )
    async def test_rechazos_senalan_el_campo(
        self,
        db_client: httpx.AsyncClient,
        auth_repository: InMemoryAuthRepository,
        configuracion_repository: InMemoryConfiguracionRepository,
        cuerpo: dict[str, str],
        campo: str,
    ) -> None:
        configuracion_repository.politica = configuracion_repository.politica.model_copy(
            update={"largo_minimo_clave": 10}
        )
        auth_repository.agregar("ana", CLAVE)
        token = await _token(db_client)

        response = await db_client.post(CAMBIAR, json=cuerpo, headers=_auth(token))

        assert response.status_code == 422
        assert response.json()["error"]["codigo"] == "clave_insegura"
        assert response.json()["error"]["detalles"][0]["campo"] == campo

    async def test_sin_sesion_responde_401(self, db_client: httpx.AsyncClient) -> None:
        response = await db_client.post(
            CAMBIAR, json={"clave_actual": CLAVE, "clave_nueva": "Nueva.Clave22"}
        )

        assert response.status_code == 401


class TestPoliticaEnElLogin:
    async def test_intentos_y_minutos_configurables(
        self,
        db_client: httpx.AsyncClient,
        auth_repository: InMemoryAuthRepository,
        configuracion_repository: InMemoryConfiguracionRepository,
    ) -> None:
        configuracion_repository.politica = PoliticaSeguridad(
            max_intentos=4, minutos_bloqueo=30, horas_sesion=2, largo_minimo_clave=8
        )
        auth_repository.agregar("ana", CLAVE)

        codigos = [
            (await db_client.post(LOGIN, json={"usuario": "ana", "clave": "mala"})).status_code
            for _ in range(4)
        ]
        ultimo = await db_client.post(LOGIN, json={"usuario": "ana", "clave": "mala"})

        assert codigos == [401, 401, 401, 423]
        assert "30 minuto" in ultimo.json()["error"]["mensaje"]

    async def test_vigencia_de_la_sesion(
        self,
        db_client: httpx.AsyncClient,
        auth_repository: InMemoryAuthRepository,
        configuracion_repository: InMemoryConfiguracionRepository,
    ) -> None:
        configuracion_repository.politica = configuracion_repository.politica.model_copy(
            update={"horas_sesion": 2}
        )
        auth_repository.agregar("ana", CLAVE)

        response = await db_client.post(LOGIN, json={"usuario": "ana", "clave": CLAVE})

        expira = datetime.fromisoformat(response.json()["expira_en"])
        restante = expira - datetime.now(UTC)
        assert timedelta(hours=1, minutes=59) < restante <= timedelta(hours=2)

    async def test_politica_publica_sin_iniciar_sesion(self, db_client: httpx.AsyncClient) -> None:
        response = await db_client.get("/api/v1/auth/politica")

        assert response.status_code == 200
        assert response.json() == {
            "max_intentos": 3,
            "minutos_bloqueo": 15,
            "largo_minimo_clave": 8,
        }


async def test_la_auditoria_del_login_esta_acotada_por_el_bloqueo(
    db_client: httpx.AsyncClient,
    auth_repository: InMemoryAuthRepository,
    auditoria_repository: InMemoryAuditoriaRepository,
) -> None:
    auth_repository.agregar("ana", CLAVE)
    auth_repository.agregar("inactiva", CLAVE, is_active=False)

    # Sin bloqueo posible: solo van a los logs (si no, cualquiera llenaría la tabla).
    for usuario in ("nadie.aqui", "inactiva", "nadie.aqui"):
        await db_client.post(LOGIN, json={"usuario": usuario, "clave": "x"})
    for _ in range(3):
        await db_client.post(LOGIN, json={"usuario": "ana", "clave": "mala"})
    for _ in range(5):  # ya bloqueada: el bloqueo quedó registrado una vez
        await db_client.post(LOGIN, json={"usuario": "ana", "clave": "mala"})
    auth_repository._set(
        replace(auth_repository.por_id(1), locked_until=None, failed_login_attempts=0)
    )
    await db_client.post(LOGIN, json={"usuario": "ana", "clave": CLAVE})

    assert [e.accion for e in auditoria_repository.eventos] == [
        "inicio_sesion_fallido",
        "inicio_sesion_fallido",
        "inicio_sesion_fallido",
        "cuenta_bloqueada",
        "inicio_sesion",
    ]
    assert {e.actor_id for e in auditoria_repository.eventos} == {1}
    assert all("nadie.aqui" not in str(e) for e in auditoria_repository.eventos)
    assert auditoria_repository.eventos[-1].actor_nombre == "Persona ana"
