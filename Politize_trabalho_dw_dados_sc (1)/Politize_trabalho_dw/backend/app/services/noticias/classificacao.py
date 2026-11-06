"""Classificação *conservadora* da natureza de uma notícia.

Regras de neutralidade:
- Nunca atribui `fato_documentado` automaticamente: isso exige revisão editorial.
- Não mede tom positivo/negativo; só o *tipo* de conteúdo, por termos explícitos.
- O padrão é `nao_classificado`. A origem fica registrada (`heuristica`/`editorial`).
- Precedência: opinião > investigação > alegação (um artigo de opinião sobre uma
  investigação continua sendo opinião).
"""
import re

from app.services.noticias.normalizacao import normalizar_texto

NATUREZAS = ("fato_documentado", "alegacao", "opiniao", "investigacao", "nao_classificado")

ROTULOS = {
    "fato_documentado": "Fato documentado",
    "alegacao": "Alegação",
    "opiniao": "Opinião",
    "investigacao": "Investigação em andamento",
    "nao_classificado": "Sem classificação",
}

AVISOS = {
    "fato_documentado": "Registro confirmado por documento ou ato oficial, conforme revisão editorial.",
    "alegacao": "Alegação feita por terceiros. Não é fato comprovado.",
    "opiniao": "Texto de opinião ou análise. Expressa o ponto de vista do autor.",
    "investigacao": "Investigação ou apuração em curso. Não implica culpa nem condenação.",
    "nao_classificado": "A natureza desta notícia ainda não foi classificada.",
}

_TERMOS = {
    "opiniao": [
        "opiniao", "editorial", "coluna", "comentario", "artigo de opiniao", "analise opiniao",
    ],
    "investigacao": [
        "investigacao", "investigado", "investigada", "inquerito", "operacao", "policia federal",
        "ministerio publico", "denuncia", "cpi", "mandado de busca", "delacao", "apuracao",
    ],
    "alegacao": [
        "acusa", "acusado", "acusada", "acusacao", "alega", "alegou", "alegacao",
        "suspeito", "suspeita", "suspeitas",
    ],
}
_ORDEM = ("opiniao", "investigacao", "alegacao")
_REGEX = {
    cat: re.compile(r"\b(?:" + "|".join(re.escape(t) for t in termos) + r")\b")
    for cat, termos in _TERMOS.items()
}


def classificar_natureza(titulo: str, resumo: str | None = None) -> str:
    texto = normalizar_texto(f"{titulo} {resumo or ''}")
    for categoria in _ORDEM:
        if _REGEX[categoria].search(texto):
            return categoria
    return "nao_classificado"
