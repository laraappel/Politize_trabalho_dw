"""Contrato dos adaptadores de fonte."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


class FonteNaoAutorizada(Exception):
    """A fonte não tem acesso autorizado verificado; a coleta é recusada."""


class ErroColeta(Exception):
    """Falha ao obter ou interpretar os dados de uma fonte autorizada."""


@dataclass
class ItemBruto:
    titulo: str
    url: str
    guid: str | None = None
    publicado_em: datetime | None = None
    resumo: str | None = None  # já limpo e truncado; None se não permitido
    categorias: list[str] = field(default_factory=list)
    assunto_padrao: tuple[str, str] | None = None  # (slug, nome) da editoria do feed
    links_html: str = ""  # HTML bruto usado só para detectar identificadores; nunca persistido


class FonteNoticias(ABC):
    slug: str
    nome: str
    dominio: str
    tipo: str = "imprensa"
    autorizada: bool = False
    permite_resumo: bool = False
    base_autorizacao: str
    url_termos: str | None = None

    @abstractmethod
    def coletar(self) -> list[ItemBruto]:
        """Retorna itens recentes. Levanta FonteNaoAutorizada ou ErroColeta."""
