from app.errors import ErroValidacao
from app.paginacao import envelope, escapar_like, inteiro, pagina
from app.services.importacao import validar_pacote
from app.services.politicos import resumo_despesas
from types import SimpleNamespace


def test_envelope_nao_inventa_pagina_quando_vazio():
    payload = envelope([], 0, 1, 10)
    assert payload["total"] == 0
    assert payload["pages"] == 0
    assert payload["items"] == []


def test_envelope_calcula_paginas():
    payload = envelope(["a"], 11, 2, 10)
    assert payload["pages"] == 2
    assert payload["page"] == 2


def test_inteiro_rejeita_fora_do_intervalo():
    try:
        inteiro({"per_page": "999"}, "per_page", maximo=50)
        assert False
    except ErroValidacao as exc:
        assert exc.codigo == "parametro_invalido"


def test_pagina_padrao():
    page, per_page = pagina({})
    assert page == 1 and per_page == 10


def test_escapar_like_nao_amplia_busca():
    assert "%" in escapar_like("100%")
    assert escapar_like("a_b") == "a\\_b"


def test_pacote_invalido():
    try:
        validar_pacote({"versao": 2, "politicos": []})
        assert False
    except ErroValidacao:
        pass


def test_resumo_despesas_nao_trata_ausencia_como_zero():
    itens = [
        SimpleNamespace(categoria="x", valor=None),
        SimpleNamespace(categoria="x", valor=10),
    ]
    r = resumo_despesas(itens)
    assert r["completo"] is False
    assert r["registros_sem_valor"] == 1
    assert str(r["soma_valores_informados"]) == "10.00"


def test_resumo_sem_registros_nao_e_zero():
    r = resumo_despesas([])
    assert r["registros"] == 0
    assert r["soma_valores_informados"] is None
