"""Cliente HTTP da API oficial da Câmara.

A API pública não exige token. Este cliente só fala com
https://dadosabertos.camara.leg.br/api/v2 e ignora qualquer outro domínio,
inclusive links de paginação que apontem para fora.
"""
import time
from urllib.parse import parse_qsl, urlsplit, urlunsplit

import requests

HOST = "dadosabertos.camara.leg.br"
PREFIXO = "/api/v2"
ITENS_MAXIMO = 100
ITENS_PADRAO = 100


class ErroCamara(Exception):
    def __init__(self, codigo: str):
        super().__init__(codigo)
        self.codigo = codigo


class ClienteCamara:
    def __init__(
        self,
        sessao=None,
        timeout=20,
        intervalo=0.4,
        tentativas=3,
        itens=ITENS_PADRAO,
        user_agent="VotoTransparente/0.1 (projeto academico; dados abertos da Camara)",
        pausa=time.sleep,
    ):
        self.sessao = sessao or requests.Session()
        self.timeout = timeout
        self.intervalo = max(0.0, float(intervalo))
        self.tentativas = max(1, int(tentativas))
        self.itens = _limitar_itens(itens)
        self.pausa = pausa
        self._requisicoes = 0
        self.headers = {
            "Accept": "application/json",
            "User-Agent": user_agent,
        }

    def obter(self, caminho: str) -> dict:
        payload = self.get_json(caminho)
        dados = payload.get("dados")
        if not isinstance(dados, dict):
            raise ErroCamara("resposta_inesperada")
        return dados

    def listar(self, caminho: str, params=None, max_paginas=None):
        url, consulta = _url_oficial(caminho)
        consulta.update(params or {})
        consulta["itens"] = _limitar_itens(consulta.get("itens", self.itens))
        paginas = 0
        vistas = set()
        while True:
            chave = (url, tuple(sorted((str(k), str(v)) for k, v in consulta.items())))
            if chave in vistas:
                raise ErroCamara("paginacao_repetida")
            vistas.add(chave)
            payload = self.get_json(url, consulta)
            dados = payload.get("dados") or []
            if isinstance(dados, dict):
                raise ErroCamara("resposta_inesperada")
            yield from dados
            paginas += 1
            if max_paginas is not None and paginas >= max_paginas:
                return
            seguinte = _href(payload, "next")
            if not seguinte:
                return
            url, consulta = _url_oficial(seguinte)
            if "itens" not in consulta:
                consulta["itens"] = self.itens
            consulta["itens"] = _limitar_itens(consulta["itens"])

    def get_json(self, caminho: str, params=None) -> dict:
        url, consulta_fixa = _url_oficial(caminho)
        consulta = dict(consulta_fixa)
        if params:
            consulta.update(params)
        if "itens" in consulta:
            consulta["itens"] = _limitar_itens(consulta["itens"])
        ultimo = "falha_rede"
        for tentativa in range(1, self.tentativas + 1):
            if self._requisicoes > 0:
                self.pausa(self.intervalo)
            self._requisicoes += 1
            try:
                resposta = self.sessao.get(
                    url,
                    params=consulta or None,
                    headers=self.headers,
                    timeout=self.timeout,
                    allow_redirects=False,
                )
            except requests.Timeout as exc:
                ultimo = "timeout"
                if tentativa == self.tentativas:
                    raise ErroCamara("timeout") from exc
                self.pausa(_espera(tentativa, None))
                continue
            except requests.RequestException as exc:
                ultimo = "falha_rede"
                if tentativa == self.tentativas:
                    raise ErroCamara("falha_rede") from exc
                self.pausa(_espera(tentativa, None))
                continue
            codigo = resposta.status_code
            if codigo == 429 or 500 <= codigo <= 599:
                ultimo = f"http_{codigo}"
                if tentativa == self.tentativas:
                    raise ErroCamara(ultimo)
                self.pausa(_espera(tentativa, resposta.headers.get("Retry-After")))
                continue
            if codigo >= 400:
                raise ErroCamara(f"http_{codigo}")
            try:
                payload = resposta.json()
            except ValueError as exc:
                raise ErroCamara("resposta_invalida") from exc
            if not isinstance(payload, dict):
                raise ErroCamara("resposta_inesperada")
            return payload
        raise ErroCamara(ultimo)


def _limitar_itens(valor) -> int:
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        return ITENS_PADRAO
    if numero < 1:
        return 1
    if numero > ITENS_MAXIMO:
        return ITENS_MAXIMO
    return numero


def _espera(tentativa: int, retry_after) -> float:
    if retry_after not in (None, ""):
        try:
            return min(max(float(retry_after), 0.0), 30.0)
        except (TypeError, ValueError):
            pass
    return float(min(2 ** (tentativa - 1), 30))


def _href(payload: dict, rel: str):
    for link in payload.get("links") or []:
        if isinstance(link, dict) and link.get("rel") == rel and link.get("href"):
            return link["href"]
    return None


def _url_oficial(caminho: str) -> tuple[str, dict]:
    if not isinstance(caminho, str) or not caminho.strip():
        raise ErroCamara("dominio_nao_autorizado")
    bruto = caminho.strip()
    if "\\" in bruto or bruto.startswith("//"):
        raise ErroCamara("dominio_nao_autorizado")
    if "://" not in bruto:
        rel = bruto if bruto.startswith("/") else f"/{bruto}"
        if not rel.startswith(PREFIXO):
            rel = PREFIXO + rel
        bruto = f"https://{HOST}{rel}"
    partes = urlsplit(bruto)
    host = (partes.hostname or "").lower()
    if (
        partes.scheme != "https"
        or host != HOST
        or partes.username
        or partes.password
        or partes.port not in (None, 443)
        or not partes.path.startswith(PREFIXO)
    ):
        raise ErroCamara("dominio_nao_autorizado")
    consulta = dict(parse_qsl(partes.query, keep_blank_values=False))
    url = urlunsplit(("https", HOST, partes.path, "", ""))
    return url, consulta
