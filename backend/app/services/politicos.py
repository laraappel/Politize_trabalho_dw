"""Listagem, filtros e perfil de políticos com relações de domínio."""
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.dominio_constantes import UFS
from app.errors import ErroValidacao
from app.extensions import db
from app.models.dominio import Despesa, Mandato, Projeto, Votacao
from app.models.politico import Politico
from app.paginacao import data_iso, envelope, escapar_like, pagina
from app.serializacao import dinheiro, iso, origem


def _texto(args, nome, maximo=80):
    bruto = (args.get(nome) or "").strip()
    if not bruto:
        return None
    if len(bruto) > maximo:
        raise ErroValidacao("parametro_invalido", f"'{nome}' excede {maximo} caracteres.")
    return bruto


def _uf(args):
    bruto = (args.get("uf") or "").strip().upper()
    if not bruto:
        return None
    if bruto not in UFS:
        raise ErroValidacao("parametro_invalido", "'uf' deve ser uma sigla de unidade da federação.")
    return bruto


def serializar_resumo(p: Politico) -> dict:
    dados = {
        "id": p.id,
        "slug": p.slug,
        "nome_completo": p.nome_completo,
        "nome_urna": p.nome_urna,
        "nome_exibicao": p.nome_exibicao,
        "cargo": p.cargo,
        "uf": p.uf,
        "municipio": p.municipio,
        "partido": p.partido,
        "id_camara": p.id_camara,
        "id_senado": p.id_senado,
    }
    dados.update(origem(p))
    return dados


def serializar_mandato(m: Mandato) -> dict:
    dados = {
        "id": m.id,
        "cargo": m.cargo,
        "esfera": m.esfera,
        "uf": m.uf,
        "municipio": m.municipio,
        "partido": m.partido,
        "legislatura": m.legislatura,
        "inicio": iso(m.inicio),
        "fim": iso(m.fim),
        "em_curso": m.fim is None,
    }
    dados.update(origem(m))
    return dados


def serializar_projeto(pr: Projeto) -> dict:
    dados = {
        "id": pr.id,
        "casa": pr.casa,
        "numero": pr.numero,
        "ano": pr.ano,
        "identificacao": _identificacao_projeto(pr),
        "ementa": pr.ementa,
        "situacao": pr.situacao,
        "data_apresentacao": iso(pr.data_apresentacao),
        "url_oficial": pr.url_oficial,
        "politico_id": pr.politico_id,
    }
    dados.update(origem(pr))
    return dados


def _identificacao_projeto(pr: Projeto):
    if pr.numero is None or pr.ano is None:
        return None
    return f"{pr.casa.upper()} {pr.numero}/{pr.ano}"


def serializar_votacao(v: Votacao) -> dict:
    dados = {
        "id": v.id,
        "identificador_externo": v.identificador_externo,
        "casa": v.casa,
        "data_votacao": iso(v.data_votacao),
        "ementa": v.ementa,
        "voto": v.voto,
        "url_oficial": v.url_oficial,
        "projeto_id": v.projeto_id,
        "politico_id": v.politico_id,
    }
    dados.update(origem(v))
    return dados


def serializar_despesa(d: Despesa) -> dict:
    dados = {
        "id": d.id,
        "categoria": d.categoria,
        "descricao": d.descricao,
        "valor": dinheiro(d.valor),
        "periodo": {"inicio": iso(d.periodo_inicio), "fim": iso(d.periodo_fim)},
        "esfera": d.esfera,
        "politico_id": d.politico_id,
        "politico": None,
    }
    if d.politico is not None:
        dados["politico"] = {
            "id": d.politico.id,
            "nome_exibicao": d.politico.nome_exibicao,
            "uf": d.politico.uf,
            "partido": d.politico.partido,
        }
    dados.update(origem(d))
    return dados


def resumo_despesas(despesas: list[Despesa]) -> dict:
    informados = [d for d in despesas if d.valor is not None]
    ausentes = len(despesas) - len(informados)
    soma = sum((d.valor for d in informados), start=0) if informados else None
    por_categoria = []
    categorias = sorted({d.categoria for d in despesas})
    for cat in categorias:
        grupo = [d for d in despesas if d.categoria == cat]
        com_valor = [d for d in grupo if d.valor is not None]
        por_categoria.append(
            {
                "categoria": cat,
                "registros": len(grupo),
                "registros_sem_valor": len(grupo) - len(com_valor),
                "soma_valores_informados": dinheiro(sum((d.valor for d in com_valor), start=0) if com_valor else None),
                "completo": all(d.valor is not None for d in grupo),
            }
        )
    return {
        "registros": len(despesas),
        "registros_sem_valor": ausentes,
        "soma_valores_informados": dinheiro(soma),
        "completo": bool(despesas) and ausentes == 0,
        "por_categoria": por_categoria,
    }


def obter(politico_id: int) -> Politico | None:
    return db.session.get(Politico, politico_id)


def listar(args) -> dict:
    q = _texto(args, "q")
    cargo = _texto(args, "cargo", maximo=80)
    partido = _texto(args, "partido", maximo=20)
    uf = _uf(args)
    page, per_page = pagina(args)

    cond = []
    if q:
        padrao = f"%{escapar_like(q)}%"
        cond.append(
            or_(
                Politico.nome_completo.ilike(padrao, escape="\\"),
                Politico.nome_urna.ilike(padrao, escape="\\"),
            )
        )
    if cargo:
        cond.append(Politico.cargo == cargo)
    if partido:
        cond.append(func.upper(Politico.partido) == partido.upper())
    if uf:
        cond.append(func.upper(Politico.uf) == uf)

    base = select(Politico).where(*cond) if cond else select(Politico)
    total = db.session.scalar(select(func.count()).select_from(base.subquery()))
    itens = db.session.scalars(
        base.order_by(Politico.nome_completo)
        .limit(per_page)
        .offset((page - 1) * per_page)
    ).all()
    return envelope([serializar_resumo(p) for p in itens], total, page, per_page)


def listar_filtros() -> dict:
    cargos = db.session.scalars(
        select(Politico.cargo).where(Politico.cargo.is_not(None)).distinct().order_by(Politico.cargo)
    ).all()
    partidos = db.session.scalars(
        select(Politico.partido).where(Politico.partido.is_not(None)).distinct().order_by(Politico.partido)
    ).all()
    ufs = db.session.scalars(
        select(Politico.uf).where(Politico.uf.is_not(None)).distinct().order_by(Politico.uf)
    ).all()
    return {
        "cargos": list(cargos),
        "partidos": list(partidos),
        "ufs": list(ufs),
    }


def detalhe(politico_id: int) -> dict | None:
    p = db.session.scalar(
        select(Politico)
        .where(Politico.id == politico_id)
        .options(
            selectinload(Politico.mandatos),
            selectinload(Politico.projetos),
            selectinload(Politico.votacoes),
            selectinload(Politico.despesas),
        )
    )
    if p is None:
        return None
    dados = serializar_resumo(p)
    dados["apelidos"] = list(p.apelidos or [])
    dados["mandatos"] = [serializar_mandato(m) for m in p.mandatos]
    dados["projetos"] = [serializar_projeto(pr) for pr in p.projetos]
    dados["votacoes"] = [serializar_votacao(v) for v in p.votacoes]
    dados["despesas"] = [serializar_despesa(d) for d in p.despesas]
    dados["resumo_financeiro"] = resumo_despesas(p.despesas)
    return dados


def listar_relacionados(politico_id: int, args, tipo: str) -> dict:
    if obter(politico_id) is None:
        raise ErroValidacao("nao_encontrado", "Político não encontrado.", 404)
    page, per_page = pagina(args)
    if tipo == "mandatos":
        base = select(Mandato).where(Mandato.politico_id == politico_id)
        ordem = Mandato.inicio.desc()
        serial = serializar_mandato
    elif tipo == "projetos":
        base = select(Projeto).where(Projeto.politico_id == politico_id)
        ordem = Projeto.data_apresentacao.desc().nulls_last()
        serial = serializar_projeto
    elif tipo == "votacoes":
        base = select(Votacao).where(Votacao.politico_id == politico_id)
        ordem = Votacao.data_votacao.desc().nulls_last()
        serial = serializar_votacao
    elif tipo == "despesas":
        base = select(Despesa).where(Despesa.politico_id == politico_id)
        categoria = _texto(args, "categoria")
        de, ate = data_iso(args, "de"), data_iso(args, "ate")
        if categoria:
            base = base.where(Despesa.categoria == categoria)
        if de:
            base = base.where(Despesa.periodo_fim >= de)
        if ate:
            base = base.where(Despesa.periodo_inicio <= ate)
        if de and ate and de > ate:
            raise ErroValidacao("parametro_invalido", "'de' não pode ser posterior a 'ate'.")
        ordem = Despesa.periodo_inicio.desc()
        serial = serializar_despesa
    else:
        raise ErroValidacao("parametro_invalido", "Tipo de relação desconhecido.")
    total = db.session.scalar(select(func.count()).select_from(base.subquery()))
    itens = db.session.scalars(base.order_by(ordem).limit(per_page).offset((page - 1) * per_page)).all()
    extra = {}
    if tipo == "despesas":
        todas = db.session.scalars(base).all()
        extra["resumo_financeiro"] = resumo_despesas(todas)
    return envelope([serial(i) for i in itens], total, page, per_page, **extra)
