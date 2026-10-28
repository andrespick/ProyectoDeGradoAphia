"""Tokens de sesión firmados con HMAC-SHA256 (biblioteca estándar).

Formato: ``base64url(JSON{sub, nombre, roles, exp}).base64url(firma)``. Sin estado en el
servidor: desactivar un usuario o cambiar su rol surte efecto en el siguiente inicio de sesión
o al vencer el token (8 horas). Rotar ``AUTH_SECRET`` invalida todos los tokens.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import asdict, dataclass

TOKEN_TTL_SECONDS = 8 * 3600


@dataclass(frozen=True)
class TokenPayload:
    sub: str
    nombre: str
    roles: list[str]
    exp: int


def issue_token(secret: str, payload: TokenPayload) -> str:
    body = _b64url(
        json.dumps(asdict(payload), separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    )
    return f"{body}.{_sign(secret, body)}"


def verify_token(secret: str, token: str, now: float | None = None) -> TokenPayload | None:
    """``None`` si la firma no coincide, el formato es inválido o el token venció."""
    try:
        body, signature = token.split(".")
        if not hmac.compare_digest(_sign(secret, body), signature):
            return None
        data = json.loads(_b64url_decode(body))
        payload = TokenPayload(
            sub=str(data["sub"]),
            nombre=str(data["nombre"]),
            roles=[str(role) for role in data["roles"]],
            exp=int(data["exp"]),
        )
    except (ValueError, KeyError, TypeError, AttributeError):
        return None
    return payload if payload.exp > (time.time() if now is None else now) else None


def _sign(secret: str, body: str) -> str:
    return _b64url(hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest())


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))
