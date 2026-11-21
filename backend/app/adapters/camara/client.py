"""Cliente HTTP da API Dados Abertos da Câmara dos Deputados (API v2)."""
import os
import time
from urllib.parse import urlparse

import requests


class CamaraAPIError(Exception):
    """Erro de comunicação ou resposta inválida da API da Câmara."""


class CamaraClient:
    BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"

    def __init__(self, timeout=None, intervalo=None, tentativas=None, session=None):
        self.timeout = timeout or int(os.getenv("CAMARA_HTTP_TIMEOUT", "20"))
        self.intervalo = intervalo if intervalo is not None else float(os.getenv("CAMARA_INTERVALO_SEGUNDOS", "0.5"))
        self.tentativas = tentativas or int(os.getenv("CAMARA_TENTATIVAS", "3"))
        self.session = session or requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": os.getenv("CAMARA_USER_AGENT", "VotoTransparente/1.0 (projeto academico)"),
        })
        self._ultima_requisicao = 0.0

    def get(self, caminho, params=None):
        url = caminho if caminho.startswith("https://") else f"{self.BASE_URL}/{caminho.lstrip('/')}"
        if urlparse(url).netloc != "dadosabertos.camara.leg.br":
            raise CamaraAPIError("Destino HTTP não permitido pelo adaptador da Câmara.")

        ultimo_erro = None
        for tentativa in range(self.tentativas):
            espera = self.intervalo - (time.monotonic() - self._ultima_requisicao)
            if espera > 0:
                time.sleep(espera)
            try:
                resposta = self.session.get(url, params=params or {}, timeout=self.timeout)
                self._ultima_requisicao = time.monotonic()
                if resposta.status_code == 429 or resposta.status_code >= 500:
                    retry = resposta.headers.get("Retry-After")
                    time.sleep(min(float(retry), 30) if retry and str(retry).isdigit() else min(2 ** tentativa, 10))
                    ultimo_erro = CamaraAPIError(f"HTTP {resposta.status_code} ao consultar {url}")
                    continue
                resposta.raise_for_status()
                try:
                    corpo = resposta.json()
                except ValueError as exc:
                    raise CamaraAPIError("A Câmara retornou uma resposta que não é JSON válido.") from exc
                if not isinstance(corpo, dict) or "dados" not in corpo:
                    raise CamaraAPIError("Formato inesperado na resposta da API da Câmara.")
                return corpo
            except requests.HTTPError as exc:
                ultimo_erro = exc
                status = exc.response.status_code if exc.response is not None else None
                if status is not None and 400 <= status < 500:
                    break
                if tentativa + 1 < self.tentativas:
                    time.sleep(min(2 ** tentativa, 10))
            except (requests.RequestException, CamaraAPIError) as exc:
                ultimo_erro = exc
                if isinstance(exc, CamaraAPIError):
                    break
                if tentativa + 1 < self.tentativas:
                    time.sleep(min(2 ** tentativa, 10))
        raise CamaraAPIError(f"Falha ao consultar {url}: {ultimo_erro}") from ultimo_erro

    def listar(self, caminho, params=None, itens=100, max_paginas=None):
        """Percorre as páginas seguindo os links fornecidos pela API."""
        if not 1 <= int(itens) <= 100:
            raise ValueError("O parâmetro itens deve estar entre 1 e 100.")

        base = dict(params or {})
        pagina = int(base.pop("pagina", 1))
        paginas_lidas = 0
        proxima_url = None
        urls_vistas = set()

        while True:
            if proxima_url:
                if proxima_url in urls_vistas:
                    break
                urls_vistas.add(proxima_url)
                corpo = self.get(proxima_url)
            else:
                corpo = self.get(
                    caminho,
                    {**base, "pagina": pagina, "itens": int(itens)}
                )

            dados = corpo.get("dados") or []
            if not isinstance(dados, list):
                raise CamaraAPIError(
                    "A listagem retornou um campo 'dados' que não é uma lista."
                )

            for item in dados:
                yield item

            paginas_lidas += 1

            if max_paginas is not None and paginas_lidas >= max_paginas:
                break

            links = corpo.get("links") or []
            proximo = next(
                (
                    link.get("href")
                    for link in links
                    if link.get("rel") == "next" and link.get("href")
                ),
                None,
            )

            if proximo:
                proxima_url = proximo
            elif not dados or len(dados) < int(itens):
                break
            else:
                pagina += 1
                proxima_url = None
