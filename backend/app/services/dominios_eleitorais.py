"""Consultas públicas aos domínios eleitorais e de transparência."""
from sqlalchemy import func, select

from app.errors import ErroValidacao
from app.extensions import db
from app.models.dominios_eleitorais_transparencia import (
    Candidatura,
    PatrimonioDeclarado,
    ProjetoCoautoria,
    PropostaCampanha,
    Remuneracao,
)
from app.models.dominio import Projeto
from app.models.partido import Partido
from app.models.politico import Politico
from app.paginacao import envelope, pagina
from app.serializacao import dinheiro, iso, origem


def _existe_politico(politico_id):
    if db.session.get(Politico, politico_id) is None:
        raise ErroValidacao("nao_encontrado", "Político não encontrado.", 404)


def listar_partidos(args):
    page, per_page = pagina(args)
    base = select(Partido)
    q = (args.get("q") or "").strip()
    if q:
        termo = f"%{q.replace('%', r'\\%').replace('_', r'\\_')}%"
        base = base.where(Partido.nome.ilike(termo, escape="\\") | Partido.sigla.ilike(termo, escape="\\"))
    total = db.session.scalar(select(func.count()).select_from(base.subquery()))
    itens = db.session.scalars(base.order_by(Partido.sigla).offset((page - 1) * per_page).limit(per_page)).all()
    return envelope([{
        "id": p.id,
        "id_camara": p.id_camara,
        "sigla": p.sigla,
        "nome": p.nome,
        "uri": p.uri,
        **origem(p),
    } for p in itens], total, page, per_page)


def detalhe_partido(partido_id):
    p = db.session.get(Partido, partido_id)
    if p is None:
        return None
    return {"id": p.id, "id_camara": p.id_camara, "sigla": p.sigla, "nome": p.nome, "uri": p.uri, **origem(p)}


def listar_candidaturas(politico_id, args):
    _existe_politico(politico_id)
    page, per_page = pagina(args)
    base = select(Candidatura).where(Candidatura.politico_id == politico_id)
    ano = args.get("ano")
    if ano:
        try:
            base = base.where(Candidatura.ano == int(ano))
        except ValueError:
            raise ErroValidacao("parametro_invalido", "'ano' deve ser um inteiro.")
    total = db.session.scalar(select(func.count()).select_from(base.subquery()))
    itens = db.session.scalars(base.order_by(Candidatura.ano.desc()).offset((page - 1) * per_page).limit(per_page)).all()
    payload = []
    for c in itens:
        payload.append({
            "id": c.id,
            "politico_id": c.politico_id,
            "partido": {"id": c.partido.id, "sigla": c.partido.sigla, "nome": c.partido.nome} if c.partido else None,
            "partido_sigla": c.sigla_partido or (c.partido.sigla if c.partido else None),
            "ano": c.ano,
            "cargo": c.cargo,
            "uf": c.uf,
            "municipio": c.municipio,
            "nome_urna": c.nome_urna,
            "numero_candidatura": c.numero_candidatura,
            "resultado": c.resultado,
            "votos": c.votos,
            **origem(c),
        })
    return envelope(payload, total, page, per_page)


def listar_propostas_candidatura(candidatura_id, args):
    c = db.session.get(Candidatura, candidatura_id)
    if c is None:
        raise ErroValidacao("nao_encontrado", "Candidatura não encontrada.", 404)
    page, per_page = pagina(args)
    base = select(PropostaCampanha).where(PropostaCampanha.candidatura_id == candidatura_id)
    total = db.session.scalar(select(func.count()).select_from(base.subquery()))
    itens = db.session.scalars(base.order_by(PropostaCampanha.id).offset((page - 1) * per_page).limit(per_page)).all()
    return envelope([{"id": p.id, "candidatura_id": p.candidatura_id, "titulo": p.titulo, "descricao": p.descricao, "tema": p.tema, **origem(p)} for p in itens], total, page, per_page)


def listar_coautorias_projeto(projeto_id, args):
    projeto = db.session.get(Projeto, projeto_id)
    if projeto is None:
        raise ErroValidacao("nao_encontrado", "Projeto não encontrado.", 404)
    page, per_page = pagina(args)
    base = select(ProjetoCoautoria).where(ProjetoCoautoria.projeto_id == projeto_id)
    total = db.session.scalar(select(func.count()).select_from(base.subquery()))
    itens = db.session.scalars(base.order_by(ProjetoCoautoria.id).offset((page - 1) * per_page).limit(per_page)).all()
    payload = [{"id": x.id, "projeto_id": x.projeto_id, "politico_id": x.politico_id, "politico": x.politico.nome_exibicao if x.politico else None, "papel": x.papel, **origem(x)} for x in itens]
    return envelope(payload, total, page, per_page)


def listar_remuneracoes(politico_id, args):
    _existe_politico(politico_id)
    page, per_page = pagina(args)
    base = select(Remuneracao).where(Remuneracao.politico_id == politico_id)
    total = db.session.scalar(select(func.count()).select_from(base.subquery()))
    itens = db.session.scalars(base.order_by(Remuneracao.periodo_inicio.desc()).offset((page - 1) * per_page).limit(per_page)).all()
    payload = [{"id": r.id, "politico_id": r.politico_id, "cargo": r.cargo, "periodo": {"inicio": iso(r.periodo_inicio), "fim": iso(r.periodo_fim)}, "valor_bruto": dinheiro(r.valor_bruto), "beneficios": dinheiro(r.beneficios), "descontos": dinheiro(r.descontos), "valor_liquido": dinheiro(r.valor_liquido), **origem(r)} for r in itens]
    return envelope(payload, total, page, per_page)


def listar_patrimonio(politico_id, args):
    _existe_politico(politico_id)
    page, per_page = pagina(args)
    base = select(PatrimonioDeclarado).where(PatrimonioDeclarado.politico_id == politico_id)
    ano = args.get("ano")
    if ano:
        try:
            base = base.where(PatrimonioDeclarado.ano_referencia == int(ano))
        except ValueError:
            raise ErroValidacao("parametro_invalido", "'ano' deve ser um inteiro.")
    total = db.session.scalar(select(func.count()).select_from(base.subquery()))
    itens = db.session.scalars(base.order_by(PatrimonioDeclarado.ano_referencia.desc()).offset((page - 1) * per_page).limit(per_page)).all()
    payload = [{"id": a.id, "politico_id": a.politico_id, "candidatura_id": a.candidatura_id, "ano_referencia": a.ano_referencia, "tipo": a.tipo, "descricao": a.descricao, "valor": dinheiro(a.valor), "localizacao": a.localizacao, **origem(a)} for a in itens]
    return envelope(payload, total, page, per_page)
