from __future__ import annotations

import pymysql
import pytest

from db.sql import ER_DUP_ENTRY, ER_ROW_IS_REFERENCED, like_pattern, mysql_error_code


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("ana", "%ana%"),
        ("50%", "%50\\%%"),
        ("a_b", "%a\\_b%"),
        ("c\\d", "%c\\\\d%"),
    ],
)
def test_like_pattern_escapa_comodines(texto: str, esperado: str) -> None:
    assert like_pattern(texto) == esperado


def test_mysql_error_code() -> None:
    assert mysql_error_code(pymysql.err.IntegrityError(1062, "Duplicate entry")) == ER_DUP_ENTRY
    assert mysql_error_code(pymysql.err.IntegrityError(1451, "referenced")) == ER_ROW_IS_REFERENCED
    assert mysql_error_code(RuntimeError("sin código")) is None
    assert mysql_error_code(RuntimeError()) is None
