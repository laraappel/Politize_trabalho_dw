from decimal import Decimal

from app.services.camara.sincronizacao import _data, _decimal, _json_chave


def test_valores_ausentes_nao_viram_zero():
    assert _decimal(None) is None
    assert _decimal(0) == Decimal("0")
    assert _decimal("12.50") == Decimal("12.50")


def test_data_ausente_permanece_nula():
    assert _data(None) is None
    assert _data("2026-05-20T00:00:00") is not None


def test_chave_hash_e_repetivel():
    registro = {"id": 10, "valor": "0.00"}
    assert _json_chave(registro) == _json_chave(registro)
