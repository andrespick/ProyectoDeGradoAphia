from __future__ import annotations

from modules.auth.passwords import DUMMY_HASH, hash_password, verify_password


def test_formato_almacenado() -> None:
    almacenado = hash_password("Clave.Segura1", iterations=1_000)

    prefijo, iteraciones, sal, hash_ = almacenado.split("$")
    assert prefijo == "pbkdf2_sha256"
    assert iteraciones == "1000"
    assert sal and hash_
    assert "Clave.Segura1" not in almacenado


def test_verifica_correcta_y_rechaza_incorrecta() -> None:
    almacenado = hash_password("Clave.Segura1", iterations=1_000)

    assert verify_password("Clave.Segura1", almacenado)
    assert not verify_password("clave.segura1", almacenado)
    assert not verify_password("", almacenado)


def test_la_misma_clave_produce_hashes_distintos() -> None:
    assert hash_password("x1234567", iterations=1_000) != hash_password(
        "x1234567", iterations=1_000
    )


def test_respeta_las_iteraciones_guardadas() -> None:
    # Un hash viejo con menos iteraciones sigue verificando aunque la constante suba.
    assert verify_password("abc12345", hash_password("abc12345", iterations=10))


def test_cadenas_malformadas_no_rompen() -> None:
    for almacenado in [
        "",
        "x",
        "pbkdf2_sha256$1000$sal",
        "otro$1000$YQ==$YQ==",
        "pbkdf2_sha256$no$YQ==$YQ==",
    ]:
        assert not verify_password("lo-que-sea", almacenado)


def test_dummy_hash_tiene_formato_valido() -> None:
    partes = DUMMY_HASH.split("$")
    assert partes[0] == "pbkdf2_sha256" and partes[1] == "100000" and len(partes) == 4
    assert not verify_password("", DUMMY_HASH)
