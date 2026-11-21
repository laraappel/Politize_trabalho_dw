"""Funções puras de normalização: URLs, texto e chave de deduplicação."""
import hashlib
import re
import unicodedata
from datetime import datetime
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_PARAMS_RASTREAMENTO = {"fbclid", "gclid", "igshid", "mc_cid", "mc_eid", "ref", "ref_src", "cmpid"}


def canonicalizar_url(url: str) -> str:
    """Remove fragmento, parâmetros de rastreamento e barra final; força https.

    A URL *original* é sempre preservada à parte; esta forma serve só para
    detectar duplicatas.
    """
    partes = urlsplit(url.strip())
    consulta = sorted(
        (k, v)
        for k, v in parse_qsl(partes.query, keep_blank_values=True)
        if not k.lower().startswith("utm_") and k.lower() not in _PARAMS_RASTREAMENTO
    )
    caminho = partes.path.rstrip("/") or "/"
    return urlunsplit(("https", partes.netloc.lower(), caminho, urlencode(consulta), ""))


def remover_acentos(texto: str) -> str:
    decomposto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in decomposto if not unicodedata.combining(c))


def normalizar_texto(texto: str) -> str:
    """Minúsculas, sem acentos, só letras/dígitos separados por espaço único."""
    sem_acento = remover_acentos(texto).lower()
    return re.sub(r"[^a-z0-9]+", " ", sem_acento).strip()


def chave_dedup(veiculo_slug: str, titulo: str, publicado_em: datetime | None) -> str:
    dia = publicado_em.date().isoformat() if publicado_em else "sem-data"
    base = f"{veiculo_slug}|{normalizar_texto(titulo)}|{dia}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def slugify(texto: str) -> str:
    return normalizar_texto(texto).replace(" ", "-")[:80]
