from __future__ import annotations

from datetime import UTC, date, datetime

from core.fechas import hoy, inicio_del_dia_utc


def test_hoy_es_el_dia_de_colombia_aunque_en_utc_ya_sea_manana() -> None:
    # 23:30 del 28 en Bogotá = 04:30 del 29 en UTC.
    assert hoy(datetime(2026, 10, 29, 4, 30, tzinfo=UTC)) == date(2026, 10, 28)
    assert hoy(datetime(2026, 10, 29, 5, 0, tzinfo=UTC)) == date(2026, 10, 29)


def test_inicio_del_dia_de_colombia_en_utc() -> None:
    assert inicio_del_dia_utc(date(2026, 10, 28)) == datetime(2026, 10, 28, 5, 0)
