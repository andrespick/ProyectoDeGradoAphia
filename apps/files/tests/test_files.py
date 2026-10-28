from __future__ import annotations

import hashlib
from pathlib import Path

import httpx
import pytest

from config import ConfigurationError, FilesSettings
from main import create_app
from storage import detect_content_type, sanitize_filename
from tests.conftest import AUTH, PDF_BYTES, PNG_BYTES, TOKEN

pytestmark = pytest.mark.anyio


async def upload(
    client: httpx.AsyncClient,
    content: bytes,
    content_type: str = "application/pdf",
    filename: str | None = "contrato-prueba.pdf",
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    request_headers = {**AUTH, "Content-Type": content_type}
    if filename:
        request_headers["X-Filename"] = filename
    request_headers.update(headers or {})
    return await client.post("/v1/files", content=content, headers=request_headers)


async def test_health_no_requiere_token(client: httpx.AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_subir_consultar_descargar_y_eliminar_pdf(client: httpx.AsyncClient) -> None:
    uploaded = await upload(client, PDF_BYTES)

    assert uploaded.status_code == 201
    stored = uploaded.json()
    file_id = stored["id"]
    assert len(file_id) == 32
    assert stored["content_type"] == "application/pdf"
    assert stored["size"] == len(PDF_BYTES)
    assert stored["sha256"] == hashlib.sha256(PDF_BYTES).hexdigest()
    assert stored["original_name"] == "contrato-prueba.pdf"

    metadata = await client.get(f"/v1/files/{file_id}/metadata", headers=AUTH)
    assert metadata.json() == stored

    downloaded = await client.get(f"/v1/files/{file_id}", headers=AUTH)
    assert downloaded.status_code == 200
    assert downloaded.content == PDF_BYTES
    assert downloaded.headers["content-type"] == "application/pdf"
    assert downloaded.headers["content-disposition"].startswith("attachment;")
    assert downloaded.headers["x-content-type-options"] == "nosniff"

    deleted = await client.delete(f"/v1/files/{file_id}", headers=AUTH)
    assert deleted.status_code == 204
    assert (await client.get(f"/v1/files/{file_id}", headers=AUTH)).status_code == 404
    assert (await client.delete(f"/v1/files/{file_id}", headers=AUTH)).status_code == 404


async def test_imagen_png_permitida(client: httpx.AsyncClient) -> None:
    response = await upload(client, PNG_BYTES, "image/png", "foto.png")

    assert response.status_code == 201
    assert response.json()["content_type"] == "image/png"


async def test_cada_subida_genera_un_id_distinto(client: httpx.AsyncClient) -> None:
    first = (await upload(client, PDF_BYTES)).json()
    second = (await upload(client, PDF_BYTES)).json()

    assert first["id"] != second["id"]


async def test_archivos_persisten_al_recrear_el_servicio(settings: FilesSettings) -> None:
    first_app = create_app(settings)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=first_app), base_url="http://a"
    ) as c:
        file_id = (await upload(c, PDF_BYTES)).json()["id"]

    # Nueva instancia sobre el mismo directorio (equivalente a recrear el contenedor).
    second_app = create_app(settings)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=second_app), base_url="http://b"
    ) as c:
        response = await c.get(f"/v1/files/{file_id}", headers=AUTH)

    assert response.status_code == 200
    assert response.content == PDF_BYTES


class TestAutenticacion:
    @pytest.mark.parametrize(
        "headers",
        [{}, {"Authorization": "Bearer incorrecto"}, {"Authorization": TOKEN}],
        ids=["sin-token", "token-incorrecto", "sin-esquema-bearer"],
    )
    async def test_operaciones_sin_token_valido_responden_401(
        self, client: httpx.AsyncClient, headers: dict[str, str]
    ) -> None:
        file_id = (await upload(client, PDF_BYTES)).json()["id"]

        responses = [
            await client.post(
                "/v1/files",
                content=PDF_BYTES,
                headers={**headers, "Content-Type": "application/pdf"},
            ),
            await client.get(f"/v1/files/{file_id}", headers=headers),
            await client.get(f"/v1/files/{file_id}/metadata", headers=headers),
            await client.delete(f"/v1/files/{file_id}", headers=headers),
        ]

        assert [r.status_code for r in responses] == [401, 401, 401, 401]
        # El archivo sigue existiendo: la eliminación no autorizada no tuvo efecto.
        assert (await client.get(f"/v1/files/{file_id}", headers=AUTH)).status_code == 200


class TestValidacion:
    @pytest.mark.parametrize(
        ("content", "content_type"),
        [
            (b"MZ\x90\x00" + b"\x00" * 60, "application/pdf"),  # ejecutable disfrazado
            (b"<html><script>alert(1)</script></html>", "application/pdf"),
            (b"texto plano cualquiera", "text/plain"),
            (b"GIF89a" + b"\x00" * 10, "image/gif"),  # imagen no incluida en la lista
            (PDF_BYTES, "image/png"),  # tipo declarado distinto del real
        ],
        ids=["exe", "html", "texto", "gif", "tipo-declarado-falso"],
    )
    async def test_rechaza_archivos_no_permitidos(
        self, client: httpx.AsyncClient, settings: FilesSettings, content: bytes, content_type: str
    ) -> None:
        response = await upload(client, content, content_type)

        assert response.status_code == 415
        assert response.json()["error"]["codigo"] == "tipo_no_permitido"
        assert _stored_files(settings.storage_dir) == []

    async def test_rechaza_archivo_demasiado_grande(
        self, client: httpx.AsyncClient, settings: FilesSettings
    ) -> None:
        response = await upload(client, PDF_BYTES + b"0" * 2048)

        assert response.status_code == 413
        assert _stored_files(settings.storage_dir) == []

    async def test_rechaza_archivo_grande_sin_content_length(
        self, client: httpx.AsyncClient, settings: FilesSettings
    ) -> None:
        async def chunks():
            yield PDF_BYTES
            for _ in range(5):
                yield b"0" * 512

        response = await client.post(
            "/v1/files", content=chunks(), headers={**AUTH, "Content-Type": "application/pdf"}
        )

        assert response.status_code == 413
        assert _stored_files(settings.storage_dir) == []

    async def test_rechaza_archivo_vacio(self, client: httpx.AsyncClient) -> None:
        response = await upload(client, b"")

        assert response.status_code == 400

    @pytest.mark.parametrize(
        "file_id",
        ["..%2F..%2Fetc%2Fpasswd", "..", "%2e%2e", "ABCDEF0123456789ABCDEF0123456789", "123"],
    )
    async def test_ids_invalidos_no_acceden_al_disco(
        self, client: httpx.AsyncClient, file_id: str
    ) -> None:
        response = await client.get(f"/v1/files/{file_id}", headers=AUTH)

        assert response.status_code == 404

    async def test_nombre_original_no_se_usa_como_ruta(
        self, client: httpx.AsyncClient, settings: FilesSettings
    ) -> None:
        response = await upload(client, PDF_BYTES, filename="..%2F..%2Fsecreto.pdf")

        assert response.status_code == 201
        assert response.json()["original_name"] == "secreto.pdf"
        for path in settings.storage_dir.rglob("*"):
            assert path.resolve().is_relative_to(settings.storage_dir.resolve())


def test_token_debil_es_rechazado(tmp_path: Path) -> None:
    for token in ["", "corto", "change-me-" + "x" * 40]:
        with pytest.raises(ConfigurationError):
            FilesSettings(storage_dir=tmp_path, service_token=token)


def test_token_desde_archivo(tmp_path: Path) -> None:
    secret = tmp_path / "token.txt"
    secret.write_text(TOKEN + "\n", encoding="utf-8")

    settings = FilesSettings.from_env(
        {"FILES_SERVICE_TOKEN_FILE": str(secret), "FILES_STORAGE_DIR": str(tmp_path)}
    )

    assert settings.service_token == TOKEN
    assert TOKEN not in repr(settings)


def test_deteccion_de_tipos() -> None:
    assert detect_content_type(PDF_BYTES) == "application/pdf"
    assert detect_content_type(PNG_BYTES) == "image/png"
    assert detect_content_type(b"\xff\xd8\xff\xe0") == "image/jpeg"
    assert detect_content_type(b"MZ") is None


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("contrato.pdf", "contrato.pdf"),
        ("C:\\Users\\x\\contrato.pdf", "contrato.pdf"),
        ("../../etc/passwd", "passwd"),
        ("nombre\x00oculto.pdf", "nombreoculto.pdf"),
        ("..", None),
        (None, None),
    ],
)
def test_sanitize_filename(raw: str | None, expected: str | None) -> None:
    assert sanitize_filename(raw) == expected


def _stored_files(root: Path) -> list[Path]:
    return [p for p in root.rglob("*") if p.is_file()]
