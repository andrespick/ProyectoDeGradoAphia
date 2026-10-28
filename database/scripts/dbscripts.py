"""Utilidades compartidas por migrate.py y seed.py (conexión y lectura de archivos SQL)."""

from __future__ import annotations

import hashlib
import os
import re
import ssl
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

import pymysql

DATABASE_DIR = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = DATABASE_DIR / "migrations"
SEEDS_DIR = DATABASE_DIR / "seeds"

_FILE_RE = re.compile(r"^(\d{4})_([a-z0-9_]+)\.sql$")


class ScriptError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ConnectionParams:
    host: str
    port: int
    database: str
    user: str
    password: str = field(repr=False)
    ssl_required: bool = False

    @classmethod
    def from_env(cls, environ: Mapping[str, str] = os.environ) -> ConnectionParams:
        """Variables ``DB_*``.

        - ``MIGRATIONS_DB_USER`` / ``MIGRATIONS_DB_PASSWORD``: usuario con permisos DDL.
        - ``*_PASSWORD_FILE``: lee la contraseña de un archivo (Docker secrets).
        - ``DB_SSL_MODE=required``: exige TLS (producción).
        """
        user = environ.get("MIGRATIONS_DB_USER") or environ.get("DB_USER")
        password = _secret(environ, "MIGRATIONS_DB_PASSWORD") or _secret(environ, "DB_PASSWORD")
        database = environ.get("DB_NAME")
        missing = [
            name
            for name, value in (("DB_NAME", database), ("DB_USER", user), ("DB_PASSWORD", password))
            if not value
        ]
        if missing:
            raise ScriptError(f"Faltan variables de entorno: {', '.join(missing)}")
        ssl_mode = environ.get("DB_SSL_MODE", "disabled").lower()
        if ssl_mode not in {"disabled", "required"}:
            raise ScriptError("DB_SSL_MODE debe ser 'disabled' o 'required'")
        return cls(
            host=environ.get("DB_HOST", "127.0.0.1"),
            port=int(environ.get("DB_PORT", "3306")),
            database=database,  # type: ignore[arg-type]
            user=user,  # type: ignore[arg-type]
            password=password,  # type: ignore[arg-type]
            ssl_required=ssl_mode == "required",
        )

    def connect(self) -> pymysql.connections.Connection:
        return pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            charset="utf8mb4",
            autocommit=False,
            connect_timeout=10,
            init_command="SET time_zone = '+00:00'",
            ssl=_tls_context() if self.ssl_required else None,
        )


def _secret(environ: Mapping[str, str], name: str) -> str | None:
    file_path = environ.get(f"{name}_FILE")
    if file_path:
        return Path(file_path).read_text(encoding="utf-8").strip()
    return environ.get(name)


def _tls_context() -> ssl.SSLContext:
    # MySQL usa un certificado autofirmado y solo es accesible en la red interna de Docker:
    # se cifra el tráfico sin validar la cadena (ver docs/despliegue/mysql.md).
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


@dataclass(frozen=True, slots=True)
class SqlFile:
    version: str
    name: str
    path: Path
    sql: str

    @property
    def checksum(self) -> str:
        return hashlib.sha256(self.sql.replace("\r\n", "\n").encode("utf-8")).hexdigest()

    @property
    def statements(self) -> list[str]:
        return split_statements(self.sql)


def discover(directory: Path) -> list[SqlFile]:
    files: list[SqlFile] = []
    seen: set[str] = set()
    for path in sorted(directory.glob("*.sql")):
        match = _FILE_RE.match(path.name)
        if not match:
            raise ScriptError(f"Nombre inválido: {path.name} (formato: 0001_descripcion.sql)")
        version, name = match.groups()
        if version in seen:
            raise ScriptError(f"Versión duplicada: {version}")
        seen.add(version)
        files.append(SqlFile(version, name, path, path.read_text(encoding="utf-8")))
    return files


def split_statements(sql: str) -> list[str]:
    """Separa sentencias terminadas en ``;`` al final de línea. Ignora comentarios ``--``.

    Limitación intencional: no admite procedimientos almacenados ni ``DELIMITER``.
    """
    statements: list[str] = []
    current: list[str] = []
    for line in sql.replace("\r\n", "\n").split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        current.append(line)
        if stripped.endswith(";"):
            statement = "\n".join(current).strip().rstrip(";").strip()
            if statement:
                statements.append(statement)
            current = []
    if "".join(current).strip():
        raise ScriptError("La última sentencia no termina en ';'")
    return statements
