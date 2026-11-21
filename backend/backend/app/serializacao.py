"""Formatos JSON compartilhados: datas ISO, dinheiro e origem dos dados."""
from datetime import date, datetime
from decimal import Decimal


def iso(valor):
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor.isoformat()
    if isinstance(valor, date):
        return valor.isoformat()
    return str(valor)


def dinheiro(valor):
    """Valor financeiro ou null. Nunca converte ausência em zero."""
    if valor is None:
        return None
    if isinstance(valor, Decimal):
        return format(valor, ".2f")
    return format(Decimal(str(valor)), ".2f")


def fonte(nome, url):
    if not nome and not url:
        return None
    return {"nome": nome, "url": url}


def origem(registro):
    codigo = getattr(registro, "origem_dados", None) or "demonstracao"
    return {
        "origem_dados": codigo,
        "demonstracao": codigo == "demonstracao",
        "fonte": fonte(getattr(registro, "fonte_nome", None), getattr(registro, "fonte_url", None)),
    }
