"""Consultas agregadas do portal da transparência (despesas públicas)."""
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.errors import ErroValidacao
from app.extensions import db
from app.models.dominio import Despesa, Mandato, Projeto, Votacao
from app.models.politico import Politico
from app.paginacao import data_iso, envelope, pagina
from app.serializacao import dinheiro
from app.services.politicos import _texto, _uf, resumo_despesas, serializar_despesa


def listar_despesas(args) -> dict:
    categoria = _texto(args, "categoria")
    uf = _uf(args)
    de, ate = data_iso(args, "de"), data_iso(args, "ate")
    if de and ate and de > ate:
        raise ErroValidacao("parametro_invalido", "'de' não pode ser posterior a 'ate'.")
    page, per_page = pagina(args)

    base = select(Despesa).options(selectinload(Despesa.politico))
    if categoria:
        base = base.where(Despesa.categoria == categoria)
    if uf:
        base = base.where(Despesa.politico_id.in_(select(Politico.id).where(func.upper(Politico.uf) == uf)))
    if de:
        base = base.where(Despesa.periodo_fim >= de)
    if ate:
        base = base.where(Despesa.periodo_inicio <= ate)

    total = db.session.scalar(select(func.count()).select_from(base.subquery()))
    itens = db.session.scalars(
        base.order_by(Despesa.periodo_inicio.desc(), Despesa.id.desc())
        .limit(per_page)
        .offset((page - 1) * per_page)
    ).all()
    todas = db.session.scalars(base.options(selectinload(Despesa.politico))).all()
    return envelope(
        [serializar_despesa(d) for d in itens],
        total,
        page,
        per_page,
        resumo_financeiro=resumo_despesas(todas),
    )


def listar_filtros() -> dict:
    categorias = db.session.scalars(
        select(Despesa.categoria).distinct().order_by(Despesa.categoria)
    ).all()
    ufs = db.session.scalars(
        select(Politico.uf)
        .where(Politico.id.in_(select(Despesa.politico_id)), Politico.uf.is_not(None))
        .distinct()
        .order_by(Politico.uf)
    ).all()
    return {"categorias": list(categorias), "ufs": list(ufs)}


def panorama() -> dict:
    politicos = db.session.scalar(select(func.count()).select_from(Politico)) or 0
    demonstracao = db.session.scalar(
        select(func.count()).select_from(Politico).where(Politico.origem_dados == "demonstracao")
    ) or 0
    despesas = db.session.scalars(select(Despesa)).all()
    return {
        "politicos": politicos,
        "politicos_demonstracao": demonstracao,
        "mandatos": db.session.scalar(select(func.count()).select_from(Mandato)) or 0,
        "projetos": db.session.scalar(select(func.count()).select_from(Projeto)) or 0,
        "votacoes": db.session.scalar(select(func.count()).select_from(Votacao)) or 0,
        "despesas": resumo_despesas(despesas),
        "aviso": "Contagens refletem o cadastro atual. Ausência de despesa não significa gasto zero.",
    }
