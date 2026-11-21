"""Contrato único de paginação e parse de inteiros/datas da API."""
from datetime import date
from math import ceil

from app.errors import ErroValidacao

PER_PAGE_PADRAO = 10
PER_PAGE_MAX = 50


def inteiro(args, nome, minimo=1, maximo=None, obrigatorio=False):
    bruto = args.get(nome)
    if bruto in (None, ""):
        if obrigatorio:
            raise ErroValidacao("parametro_invalido", f"'{nome}' é obrigatório.")
        return None
    try:
        valor = int(bruto)
    except (TypeError, ValueError):
        raise ErroValidacao("parametro_invalido", f"'{nome}' deve ser um inteiro.")
    if valor < minimo or (maximo is not None and valor > maximo):
        raise ErroValidacao("parametro_invalido", f"'{nome}' fora do intervalo permitido.")
    return valor


def data_iso(args, nome):
    bruto = args.get(nome)
    if not bruto:
        return None
    try:
        return date.fromisoformat(bruto)
    except (TypeError, ValueError):
        raise ErroValidacao("parametro_invalido", f"'{nome}' deve estar no formato AAAA-MM-DD.")


def pagina(args, padrao=PER_PAGE_PADRAO):
    page = inteiro(args, "page") or 1
    per_page = inteiro(args, "per_page", maximo=PER_PAGE_MAX) or padrao
    return page, per_page


def envelope(items, total, page, per_page, **extra):
    pages = ceil(total / per_page) if total and per_page else 0
    payload = {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
    }
    payload.update(extra)
    return payload


def escapar_like(valor: str) -> str:
    return valor.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
