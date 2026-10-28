from __future__ import annotations

import time

from modules.auth.tokens import TokenPayload, issue_token, verify_token

SECRET = "s" * 32


def _payload(**overrides: object) -> TokenPayload:
    values: dict[str, object] = {
        "sub": "7",
        "nombre": "Ñandú Pérez",
        "roles": ["asesor"],
        "exp": int(time.time()) + 60,
    }
    values.update(overrides)
    return TokenPayload(**values)  # type: ignore[arg-type]


def test_ida_y_vuelta_conserva_el_contenido() -> None:
    token = issue_token(SECRET, _payload())

    assert verify_token(SECRET, token) == _payload(exp=verify_token(SECRET, token).exp)  # type: ignore[union-attr]
    assert verify_token(SECRET, token).nombre == "Ñandú Pérez"  # type: ignore[union-attr]


def test_rechaza_cuerpo_o_firma_manipulados() -> None:
    token = issue_token(SECRET, _payload())
    body, signature = token.split(".")
    otro = issue_token(SECRET, _payload(roles=["admin_sistemas"])).split(".")[0]

    assert verify_token(SECRET, f"{otro}.{signature}") is None
    assert verify_token(SECRET, f"{body}.{signature[:-2]}AA") is None
    assert verify_token(SECRET, body) is None
    assert verify_token(SECRET, "") is None
    assert verify_token(SECRET, "a.b.c") is None


def test_rechaza_otro_secreto_y_expirado() -> None:
    token = issue_token(SECRET, _payload())
    expirado = issue_token(SECRET, _payload(exp=int(time.time()) - 1))

    assert verify_token("x" * 32, token) is None
    assert verify_token(SECRET, expirado) is None
    assert verify_token(SECRET, token, now=time.time() + 120) is None
