"""Hash de contraseñas con PBKDF2-HMAC-SHA256 (biblioteca estándar; funciona en Pyodide).

Formato almacenado en ``user_account.hashed_password``::

    pbkdf2_sha256$<iteraciones>$<sal_base64>$<hash_base64>

La verificación respeta las iteraciones guardadas, así que el coste puede subir en el futuro
sin invalidar las contraseñas existentes.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

try:
    from hashlib import pbkdf2_hmac as _pbkdf2_hmac
except ImportError:  # Pyodide (Cloudflare Workers) no incluye pbkdf2_hmac: ver _pbkdf2_sha256
    _pbkdf2_hmac = None

# Medido en Workers local (ver docs/seguridad/README.md). Subirlo encarece cada inicio de sesión.
PBKDF2_ITERATIONS = 100_000
_PREFIX = "pbkdf2_sha256"
_SALT_BYTES = 16
_DKLEN = 32

# Hash de una clave aleatoria desechada: se verifica contra él cuando el usuario no existe o
# está inactivo, para que el tiempo de respuesta no revele si la cuenta existe.
# Es un literal para no gastar CPU al importar el módulo en el arranque del Worker.
DUMMY_HASH = (
    "pbkdf2_sha256$100000$rcIDyz5yDdTwHGWIMcjzmw==$Um92ltLM5xpxrMkyJW3XNay7dGQ8Ox941itlT2JTnqs="
)


def hash_password(clave: str, iterations: int = PBKDF2_ITERATIONS) -> str:
    salt = secrets.token_bytes(_SALT_BYTES)
    derived = _derive(clave, salt, iterations)
    return (
        f"{_PREFIX}${iterations}${base64.b64encode(salt).decode()}$"
        f"{base64.b64encode(derived).decode()}"
    )


def verify_password(clave: str, almacenado: str) -> bool:
    try:
        prefix, iterations_text, salt_b64, hash_b64 = almacenado.split("$")
        iterations = int(iterations_text)
        salt = base64.b64decode(salt_b64, validate=True)
        expected = base64.b64decode(hash_b64, validate=True)
    except (ValueError, TypeError):
        return False
    if prefix != _PREFIX or iterations < 1 or not salt or not expected:
        return False
    return hmac.compare_digest(_derive(clave, salt, iterations), expected)


def _derive(clave: str, salt: bytes, iterations: int) -> bytes:
    password = clave.encode("utf-8")
    if _pbkdf2_hmac is not None:
        return _pbkdf2_hmac("sha256", password, salt, iterations, _DKLEN)
    return _pbkdf2_sha256(password, salt, iterations)


def _pbkdf2_sha256(password: bytes, salt: bytes, iterations: int) -> bytes:
    """PBKDF2-HMAC-SHA256 (RFC 8018) para un bloque de 32 bytes, sin ``pbkdf2_hmac``.

    HMAC con estados interno/externo precalculados y copiados en cada iteración: es la forma
    más rápida posible en Python puro (la que usaba CPython antes de delegar en OpenSSL).
    """
    if len(password) > 64:
        password = hashlib.sha256(password).digest()
    password = password.ljust(64, b"\x00")
    inner = hashlib.sha256(bytes(byte ^ 0x36 for byte in password))
    outer = hashlib.sha256(bytes(byte ^ 0x5C for byte in password))

    def prf(message: bytes) -> bytes:
        i = inner.copy()
        i.update(message)
        o = outer.copy()
        o.update(i.digest())
        return o.digest()

    block = prf(salt + b"\x00\x00\x00\x01")
    result = int.from_bytes(block, "big")
    for _ in range(iterations - 1):
        block = prf(block)
        result ^= int.from_bytes(block, "big")
    return result.to_bytes(_DKLEN, "big")
