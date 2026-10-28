"""Normalización de texto compartida por los esquemas de entrada (Pydantic)."""

from __future__ import annotations

import re
import unicodedata

# Validación sintáctica conservadora; no comprueba que el buzón exista.
EMAIL_RE = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
)


def normalizar_nombre(value: str) -> str:
    """Rechaza caracteres de control y colapsa espacios repetidos."""
    if any(unicodedata.category(char).startswith("C") for char in value):
        raise ValueError("El nombre contiene caracteres no permitidos")
    return " ".join(value.split())


def normalizar_correo(value: str) -> str:
    if not EMAIL_RE.fullmatch(value):
        raise ValueError("El correo electrónico no es válido")
    return value.lower()
