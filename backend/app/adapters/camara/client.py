
import os
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

import requests


class CamaraAPIError(Exception):
    """Erro de comunicação ou resposta inválida da API da Câmara."""


class CamaraClient:
    BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"

    def __init__(
        self,
        timeout=None,
        intervalo=None,
        tentativas=None,
        session=None,
    ):
        self.timeout = timeout or int(
            os.getenv("CAMARA_HTTP_TIMEOUT", "40")
        )

        self.intervalo = (
            intervalo
            if intervalo is not None
            else float(os.getenv("CAMARA_INTERVALO_SEGUNDOS", "0.5"))
        )

        self.tentativas = (
            tentativas
            if tentativas is not None
            else int(os.getenv("CAMARA_TENTATIVAS", "5"))
        )

        if self.tentativas < 1:
            raise ValueError("CAMARA_TENTATIVAS deve ser maior que zero.")

        self.session = session or requests.Session()

        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": os.getenv(
                "CAMARA_USER_AGENT",
                "VotoTransparente/1.0 (projeto academico)",
            ),
        })

        self._ultima_requisicao = 0.0

    def _esperar_intervalo(self):
        espera = self.intervalo - (
            time.monotonic() - self._ultima_requisicao
        )

        if espera > 0:
            time.sleep(espera)

    @staticmethod
    def _espera_retentativa(resposta, tentativa):
        """Calcula espera progressiva, respeitando Retry-After."""
        retry = resposta.headers.get("Retry-After") if resposta else None

        if retry:
            try:
                return min(max(float(retry), 0), 60)
            except ValueError:
                try:
                    data = parsedate_to_datetime(retry)

                    if data.tzinfo is None:
                        data = data.replace(tzinfo=timezone.utc)

                    segundos = (
                        data - datetime.now(timezone.utc)
                    ).total_seconds()

                    return min(max(segundos, 0), 60)
                except (TypeError, ValueError, OverflowError):
                    pass

        return min(2 ** tentativa, 30)

    def get(self, caminho, params=None, ignorar_404=False):
        url = (
            caminho
            if caminho.startswith("https://")
            else f"{self.BASE_URL}/{caminho.lstrip('/')}"
        )

        if urlparse(url).netloc != "dadosabertos.camara.leg.br":
            raise CamaraAPIError(
                "Destino HTTP não permitido pelo adaptador da Câmara."
            )

        ultimo_erro = None

        for tentativa in range(self.tentativas):
            self._esperar_intervalo()

            resposta = None

            try:
                resposta = self.session.get(
                    url,
                    params=params or {},
                    timeout=self.timeout,
                )

                self._ultima_requisicao = time.monotonic()

                if resposta.status_code == 404 and ignorar_404:
                    return {"dados": []}

                if resposta.status_code == 429 or resposta.status_code in (
                    500, 502, 503, 504
                ):
                    ultimo_erro = requests.HTTPError(
                        f"HTTP {resposta.status_code}",
                        response=resposta,
                    )

                    if tentativa + 1 < self.tentativas:
                        espera = self._espera_retentativa(
                            resposta,
                            tentativa,
                        )
                        print(
                            f"Câmara respondeu HTTP "
                            f"{resposta.status_code}. "
                            f"Tentativa {tentativa + 1}/"
                            f"{self.tentativas}. "
                            f"Aguardando {espera:.0f}s...",
                            flush=True,
                        )
                        time.sleep(espera)
                        continue

                    break

                resposta.raise_for_status()

                try:
                    corpo = resposta.json()
                except ValueError as exc:
                    raise CamaraAPIError(
                        "A Câmara retornou uma resposta que não é JSON válido."
                    ) from exc

                if not isinstance(corpo, dict) or "dados" not in corpo:
                    raise CamaraAPIError(
                        "Formato inesperado na resposta da API da Câmara."
                    )

                return corpo

            except requests.RequestException as exc:
                ultimo_erro = exc

                if tentativa + 1 < self.tentativas:
                    espera = min(2 ** tentativa, 30)

                    print(
                        f"Falha de comunicação com a Câmara. "
                        f"Tentativa {tentativa + 1}/"
                        f"{self.tentativas}. "
                        f"Aguardando {espera}s...",
                        flush=True,
                    )

                    time.sleep(espera)

            except CamaraAPIError:
                raise

        raise CamaraAPIError(
            f"Falha ao consultar {url}: {ultimo_erro}"
        ) from ultimo_erro

    def get_opcional(self, caminho, params=None):
        """Consulta endpoints que podem retornar 404."""
        return self.get(
            caminho,
            params=params,
            ignorar_404=True,
        )

    def listar(
        self,
        caminho,
        params=None,
        itens=100,
        max_paginas=None,
    ):
        if not 1 <= int(itens) <= 100:
            raise ValueError(
                "O parâmetro itens deve estar entre 1 e 100."
            )

        base = dict(params or {})
        pagina = int(base.pop("pagina", 1))
        paginas_lidas = 0

        while True:
            corpo = self.get(
                caminho,
                {
                    **base,
                    "pagina": pagina,
                    "itens": int(itens),
                },
            )

            dados = corpo.get("dados") or []

            if not isinstance(dados, list):
                raise CamaraAPIError(
                    "A listagem retornou um campo "
                    "'dados' que não é uma lista."
                )

            yield from dados
            paginas_lidas += 1

            if not dados or len(dados) < int(itens):
                break

            if (
                max_paginas is not None
                and paginas_lidas >= max_paginas
            ):
                break

            pagina += 1
