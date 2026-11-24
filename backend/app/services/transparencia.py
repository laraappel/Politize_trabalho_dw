"""Consultas agregadas do portal da transpar?ncia."""
from sqlalchemy import func, select

from app.extensions import db
from app.models.dominio import Mandato, Projeto, Votacao
from app.models.politico import Politico
from app.paginacao import envelope, pagina
from app.services.despesas import (
    _consulta_unificada_despesas,
    listar_despesas_paginadas,
)


def listar_despesas(args) -> dict:
    page, per_page = pagina(args)
    itens, total, resumo = listar_despesas_paginadas(args, page, per_page)

    return envelope(
        itens,
        total,
        page,
        per_page,
        resumo_financeiro=resumo,
    )


def listar_filtros() -> dict:
    despesas = _consulta_unificada_despesas()
    categorias = db.session.scalars(
        select(despesas.c.categoria).where(despesas.c.categoria.is_not(None)).distinct().order_by(despesas.c.categoria)
    ).all()
    ufs = db.session.scalars(
        select(despesas.c.uf).where(despesas.c.uf.is_not(None)).distinct().order_by(despesas.c.uf)
    ).all()

    return {
        "categorias": categorias,
        "ufs": ufs,
    }


def panorama() -> dict:
    politicos = db.session.scalar(
        select(func.count()).select_from(Politico)
    ) or 0

    demonstracao = db.session.scalar(
        select(func.count())
        .select_from(Politico)
        .where(Politico.origem_dados == "demonstracao")
    ) or 0

    _, _, despesas = listar_despesas_paginadas({}, 1, 1)

    return {
        "politicos": politicos,
        "politicos_demonstracao": demonstracao,
        "mandatos": db.session.scalar(
            select(func.count()).select_from(Mandato)
        ) or 0,
        "projetos": db.session.scalar(
            select(func.count()).select_from(Projeto)
        ) or 0,
        "votacoes": db.session.scalar(
            select(func.count()).select_from(Votacao)
        ) or 0,
        "despesas": despesas,
        "aviso": (
            "Contagens refletem o cadastro atual. "
            "Aus?ncia de despesa n?o significa gasto zero."
        ),
    }
