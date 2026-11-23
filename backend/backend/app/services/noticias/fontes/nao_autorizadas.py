"""Adaptadores bloqueados: veículos para os quais NÃO foi confirmada uma forma
autorizada de acesso (API, RSS com licença de redistribuição ou parceria).

Eles existem para que a limitação fique registrada e visível. Não fazem requisições
e não geram dados. Para habilitar um veículo: leia os termos oficiais, obtenha
licença/chave se exigida e implemente `coletar()`.
"""
from app.services.noticias.fontes.base import FonteNaoAutorizada, FonteNoticias

_MOTIVO = (
    "Acesso autorizado não confirmado: não foi verificada, em documentação oficial, uma API ou "
    "RSS com licença para redistribuir metadados. Coleta desativada até haver licença, "
    "parceria ou termos que a permitam."
)


class _Bloqueada(FonteNoticias):
    autorizada = False
    permite_resumo = False
    base_autorizacao = _MOTIVO

    def coletar(self):
        raise FonteNaoAutorizada(f"{self.nome}: {_MOTIVO}")


class G1(_Bloqueada):
    slug, nome, dominio = "g1", "G1", "g1.globo.com"


class CnnBrasil(_Bloqueada):
    slug, nome, dominio = "cnn-brasil", "CNN Brasil", "cnnbrasil.com.br"


class FolhaDeSPaulo(_Bloqueada):
    slug, nome, dominio = "folha", "Folha de S.Paulo", "folha.uol.com.br"
