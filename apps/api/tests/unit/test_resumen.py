from __future__ import annotations

import httpx
import pytest

from tests.conftest import bearer

pytestmark = pytest.mark.anyio


async def test_devuelve_los_conteos(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/resumen")

    assert response.status_code == 200
    body = response.json()
    assert body["personas"] == {"total": 6, "propietarios": 2, "arrendatarios": 2, "codeudores": 3}
    assert body["usuarios"] == {"total": 3, "activos": 3, "bloqueados": 0}
    assert body["contratos"]["por_vencer_60"] == 1


async def test_cualquier_rol_puede_leerlo_pero_no_un_anonimo(db_client: httpx.AsyncClient) -> None:
    from modules.auth.schemas import Role

    assert (await db_client.get("/api/v1/resumen")).status_code == 401
    asesor = await db_client.get("/api/v1/resumen", headers=bearer("3", (Role.ASESOR,)))
    assert asesor.status_code == 200
