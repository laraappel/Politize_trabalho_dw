from app.adapters.camara.client import CamaraClient


class RespostaFake:
    status_code = 200
    headers = {}

    def __init__(self, corpo):
        self.corpo = corpo

    def raise_for_status(self):
        return None

    def json(self):
        return self.corpo


class SessaoFake:
    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.headers = {}
        self.chamadas = []

    def get(self, url, params=None, timeout=None):
        self.chamadas.append((url, params, timeout))
        return RespostaFake(self.respostas.pop(0))


def test_paginacao_respeita_limite_e_busca_paginas():
    sessao = SessaoFake([
        {"dados": [{"id": 1}, {"id": 2}]},
        {"dados": [{"id": 3}]},
    ])
    cliente = CamaraClient(session=sessao, intervalo=0, tentativas=1)
    dados = list(cliente.listar("deputados", itens=2))
    assert [item["id"] for item in dados] == [1, 2, 3]
    assert sessao.chamadas[0][1]["pagina"] == 1
    assert sessao.chamadas[1][1]["pagina"] == 2
    assert all(chamada[1]["itens"] == 2 for chamada in sessao.chamadas)


def test_cliente_nao_permite_mais_de_cem_itens():
    cliente = CamaraClient(session=SessaoFake([]), intervalo=0, tentativas=1)
    try:
        list(cliente.listar("deputados", itens=101))
        assert False, "deveria rejeitar itens acima do limite"
    except ValueError as exc:
        assert "100" in str(exc)
