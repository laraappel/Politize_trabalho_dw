"""Adaptador da Agência Brasil (EBC) via RSS público.

Base de autorização: o serviço "Acessar notícias em tempo real gratuitamente"
(gov.br) informa que o conteúdo jornalístico da Agência Brasil é de livre acesso
e pode ser reproduzido desde que a Agência Brasil seja citada. Há exceção para
conteúdo de agências internacionais parceiras: nesses casos não guardamos resumo.

Guardamos apenas título, link, data, editoria e um resumo curto. Sempre
apontamos para a matéria original.

ATENÇÃO: as URLs dos feeds seguem o padrão publicado pela EBC
(`/rss/<editoria>/feed.xml`). Confirme-as no primeiro uso; um 404 gera erro claro.
"""
import html
import os
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit

import requests
from defusedxml import ElementTree as ET

from app.services.noticias.fontes.base import ErroColeta, FonteNoticias, ItemBruto
from app.services.noticias.normalizacao import slugify

_NS_DC = "{http://purl.org/dc/elements/1.1/}"
_RE_AGENCIAS_PARCEIRAS = re.compile(r"\b(Reuters|AFP|EFE|Associated Press|Agence France)\b", re.I)
_EDITORIAS_NOMES = {"politica": "Política", "justica": "Justiça", "economia": "Economia"}


def limpar_resumo(html_bruto: str | None, max_chars: int) -> str | None:
    if not html_bruto:
        return None
    texto = re.sub(r"<[^>]+>", " ", html_bruto)  # remove tags e pixels de rastreamento
    texto = re.sub(r"\s+", " ", html.unescape(texto)).strip()
    if not texto:
        return None
    if len(texto) <= max_chars:
        return texto
    corte = texto[:max_chars].rsplit(" ", 1)[0].rstrip(".,;:- ")
    return corte + "…"


def _parse_data(texto: str | None) -> datetime | None:
    if not texto:
        return None
    try:
        dt = parsedate_to_datetime(texto.strip())
    except (TypeError, ValueError):
        try:
            dt = datetime.fromisoformat(texto.strip().replace("Z", "+00:00"))
        except ValueError:
            return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def parse_rss(conteudo: bytes, editoria: str, dominio: str, max_resumo: int = 300) -> list[ItemBruto]:
    """Interpreta um RSS 2.0. Função pura, testável sem rede."""
    try:
        raiz = ET.fromstring(conteudo)
    except Exception as exc:  # XML inválido ou construção maliciosa bloqueada pelo defusedxml
        raise ErroColeta(f"RSS inválido: {exc}") from exc

    assunto = (slugify(editoria), _EDITORIAS_NOMES.get(editoria, editoria.replace("-", " ").title()))
    itens = []
    for el in raiz.iter("item"):
        titulo = (el.findtext("title") or "").strip()
        link = (el.findtext("link") or "").strip()
        if not titulo or not link:
            continue
        host = (urlsplit(link).hostname or "").lower()
        if host != dominio and not host.endswith("." + dominio):
            continue  # ignora links que não pertencem ao veículo
        descricao = el.findtext("description") or ""
        resumo = None if _RE_AGENCIAS_PARCEIRAS.search(descricao) else limpar_resumo(descricao, max_resumo)
        data = _parse_data(el.findtext("pubDate")) or _parse_data(el.findtext(f"{_NS_DC}date"))
        itens.append(
            ItemBruto(
                titulo=html.unescape(titulo),
                url=link,
                guid=(el.findtext("guid") or "").strip() or None,
                publicado_em=data,
                resumo=resumo,
                categorias=[c.text.strip() for c in el.findall("category") if c.text],
                assunto_padrao=assunto,
                links_html=descricao,
            )
        )
    return itens


class AgenciaBrasil(FonteNoticias):
    slug = "agencia-brasil"
    nome = "Agência Brasil"
    dominio = "agenciabrasil.ebc.com.br"
    tipo = "agencia_publica"
    autorizada = True
    permite_resumo = True
    base_autorizacao = (
        "Serviço gov.br 'Acessar notícias em tempo real gratuitamente': conteúdo livre e "
        "reprodução permitida com crédito à Agência Brasil; exceto conteúdo de agências "
        "internacionais parceiras (não guardamos resumo desses itens). Agência pública (EBC): "
        "ver nota de pluralidade em docs/NOTICIAS.md."
    )
    url_termos = "https://www.gov.br/pt-br/servicos/acessar-noticias-em-tempo-real-gratuitamente"

    def __init__(self, editorias=None, timeout=None, user_agent=None, max_resumo=None):
        env = os.getenv("AGENCIA_BRASIL_EDITORIAS", "politica,justica")
        self.editorias = editorias or [e.strip() for e in env.split(",") if e.strip()]
        self.timeout = timeout or float(os.getenv("NOTICIAS_HTTP_TIMEOUT", "15"))
        self.user_agent = user_agent or os.getenv(
            "NOTICIAS_USER_AGENT", "VotoTransparenteBot/0.1 (projeto academico; leitura de RSS publico)"
        )
        self.max_resumo = max_resumo or int(os.getenv("NOTICIAS_RESUMO_MAX_CHARS", "300"))

    def url_feed(self, editoria: str) -> str:
        return f"https://{self.dominio}/rss/{editoria}/feed.xml"

    def coletar(self) -> list[ItemBruto]:
        itens: list[ItemBruto] = []
        erros = []
        for editoria in self.editorias:
            try:
                resp = requests.get(
                    self.url_feed(editoria),
                    headers={"User-Agent": self.user_agent, "Accept": "application/rss+xml, application/xml"},
                    timeout=self.timeout,
                )
                resp.raise_for_status()
                itens.extend(parse_rss(resp.content, editoria, self.dominio, self.max_resumo))
            except (requests.RequestException, ErroColeta) as exc:
                erros.append(f"{editoria}: {exc}")
        if erros and not itens:
            raise ErroColeta("; ".join(erros))
        return itens
