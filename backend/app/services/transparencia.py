"""Consultas agregadas do portal da transpar?ncia."""
from sqlalchemy import func, select

from app.extensions import db
from app.models.dominio import Mandato, Projeto, Votacao
from app.models.politico import Politico
from app.paginacao import envelope, pagina
from app.services.despesas import (
    listar_despesas_unificadas,
    resumo_financeiro,
)


def listar_despesas(args) -> dict:
    todas = listar_despesas_unificadas(args=args)
    total = len(todas)
    page, per_page = pagina(args)
    inicio = (page - 1) * per_page

    return envelope(
        todas[inicio:inicio + per_page],
        total,
        page,
        per_page,
        resumo_financeiro=resumo_financeiro(todas),
    )


def listar_filtros() -> dict:
    despesas = listar_despesas_unificadas()

    categorias = sorted({
        item["categoria"]
        for item in despesas
        if item.get("categoria")
    })
    ufs = sorted({
        item["politico"]["uf"]
        for item in despesas
        if item.get("politico") and item["politico"].get("uf")
    })

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

    despesas = listar_despesas_unificadas()

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
        "despesas": resumo_financeiro(despesas),
        "aviso": (
            "Contagens refletem o cadastro atual. "
            "Aus?ncia de despesa n?o significa gasto zero."
        ),
    }
