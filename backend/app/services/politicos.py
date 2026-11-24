"""Listagem, filtros e perfil de políticos com relações de domínio."""
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload
import re

from app.dominio_constantes import UFS
from app.errors import ErroValidacao
from app.extensions import db
from app.models.dominio import Despesa, Mandato, Projeto, Votacao
from app.models.camara import HistoricoCamara, MandatoCamara
from app.models.cargo_eletivo import CargoEletivo
from app.models.dominios_eleitorais_transparencia import Candidatura
from app.models.politico import Politico
from app.paginacao import data_iso, envelope, escapar_like, pagina
from app.serializacao import dinheiro, iso, origem
from app.services.despesas import listar_despesas_unificadas, resumo_financeiro


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
    dados["ano_referencia"] = _ano_fonte_politico(p) if p.origem_dados == "oficial" else None
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
    dados["ano_referencia"] = m.inicio.year if m.inicio else None
    return dados


def _ano_referencia(valor):
    return valor.year if valor else None


def _ano_fonte_politico(p: Politico):
    match = re.search(r"candidatos-(\d{4})", p.fonte_url or "")
    if match:
        return int(match.group(1))
    return _ano_referencia(p.atualizado_em or p.coletado_em)


def _serializar_cargo_oficial(item: CargoEletivo) -> dict:
    return {
        "id": item.id,
        "cargo": item.cargo,
        "esfera": item.esfera,
        "partido": item.partido,
        "uf": item.uf,
        "municipio": item.municipio,
        "ano_eleicao": item.ano_eleicao,
        "ano_inicio": item.ano_inicio,
        "ano_fim": item.ano_fim,
        "situacao": item.situacao,
        "origem": item.origem,
        "ano_referencia": item.ano_eleicao or _ano_referencia(item.atualizado_em),
        "fonte": {"nome": item.fonte_nome, "url": item.fonte_url},
    }


def _serializar_candidatura_oficial(item: Candidatura) -> dict:
    return {
        "id": item.id,
        "cargo": item.cargo,
        "partido": item.sigla_partido or (item.partido.sigla if item.partido else None),
        "uf": item.uf,
        "municipio": item.municipio,
        "ano_eleicao": item.ano,
        "situacao": item.resultado,
        "nome_urna": item.nome_urna,
        "numero_candidatura": item.numero_candidatura,
        "ano_referencia": item.ano,
        "fonte": {"nome": item.fonte_nome, "url": item.fonte_url},
    }


def _perfil_oficial(p: Politico) -> dict:
    cargos = db.session.scalars(
        select(CargoEletivo)
        .where(CargoEletivo.politico_id == p.id, CargoEletivo.fonte_url.is_not(None))
        .order_by(CargoEletivo.ano_eleicao.desc().nullslast(), CargoEletivo.atualizado_em.desc())
    ).all()
    candidaturas = db.session.scalars(
        select(Candidatura)
        .where(
            Candidatura.politico_id == p.id,
            Candidatura.origem_dados == "oficial",
            Candidatura.fonte_nome.is_not(None),
            Candidatura.fonte_url.is_not(None),
        )
        .order_by(Candidatura.ano.desc(), Candidatura.cargo)
    ).all()
    mandatos = db.session.scalars(
        select(Mandato)
        .where(
            Mandato.politico_id == p.id,
            Mandato.origem_dados == "oficial",
            Mandato.fonte_nome.is_not(None),
            Mandato.fonte_url.is_not(None),
        )
        .order_by(Mandato.inicio.desc())
    ).all()

    mandatos_camara = []
    eventos_camara = []
    if p.id_camara is not None:
        mandatos_camara = db.session.scalars(
            select(MandatoCamara)
            .where(MandatoCamara.politico_id == p.id)
            .order_by(MandatoCamara.data_inicio.desc().nullslast())
        ).all()
        eventos_camara = db.session.scalars(
            select(HistoricoCamara)
            .where(HistoricoCamara.politico_id == p.id)
            .order_by(HistoricoCamara.data_hora.desc().nullslast(), HistoricoCamara.id.desc())
        ).all()

    fonte_camara = "https://dadosabertos.camara.leg.br/api/v2/deputados"
    historico_camara = f"{fonte_camara}/{p.id_camara}/historico" if p.id_camara else None
    mandatos_payload = [{
        "cargo": "Deputado federal",
        "esfera": "federal",
        "legislatura": item.id_legislatura,
        "inicio": iso(item.data_inicio),
        "fim": iso(item.data_fim),
        "partido": item.partido_sigla,
        "uf": item.uf,
        "situacao": item.situacao,
        "ano_referencia": _ano_referencia(item.data_inicio) or _ano_referencia(item.data_fim),
        "fonte": {"nome": "Câmara dos Deputados", "url": historico_camara},
    } for item in mandatos_camara]
    mandatos_payload.extend(serializar_mandato(item) for item in mandatos)

    eventos_payload = [{
        "legislatura": item.id_legislatura,
        "data": iso(item.data_hora),
        "nome": item.nome_eleitoral or item.nome,
        "partido": item.sigla_partido,
        "uf": item.sigla_uf,
        "situacao": item.situacao,
        "condicao_eleitoral": item.condicao_eleitoral,
        "descricao_status": item.descricao_status,
        "ano_referencia": _ano_referencia(item.data_hora),
        "fonte": {
            "nome": "Câmara dos Deputados",
            "url": item.uri_origem or historico_camara,
        },
    } for item in eventos_camara]

    identificacao = None
    if p.origem_dados == "oficial" and p.fonte_nome and p.fonte_url:
        identificacao = {
            "cargo": p.cargo,
            "partido": p.partido,
            "uf": p.uf,
            "municipio": p.municipio,
            "ano_referencia": _ano_fonte_politico(p),
            "fonte": {"nome": p.fonte_nome, "url": p.fonte_url},
        }

    return {
        "identificacao": identificacao,
        "cargos": [_serializar_cargo_oficial(item) for item in cargos],
        "candidaturas": [_serializar_candidatura_oficial(item) for item in candidaturas],
        "mandatos": mandatos_payload,
        "historico": eventos_payload,
    }


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
        )
    )
    if p is None:
        return None

    dados = serializar_resumo(p)
    dados["apelidos"] = list(p.apelidos or [])
    dados["dados_oficiais"] = _perfil_oficial(p)
    dados["mandatos"] = [serializar_mandato(m) for m in p.mandatos]
    dados["projetos"] = [serializar_projeto(pr) for pr in p.projetos]
    dados["votacoes"] = [serializar_votacao(v) for v in p.votacoes]

    despesas = listar_despesas_unificadas(politico_id=politico_id)
    dados["despesas"] = despesas
    dados["resumo_financeiro"] = resumo_financeiro(despesas)
    return dados


def listar_relacionados(politico_id: int, args, tipo: str) -> dict:
    if obter(politico_id) is None:
        raise ErroValidacao("nao_encontrado", "Pol?tico n?o encontrado.", 404)

    page, per_page = pagina(args)

    if tipo == "despesas":
        todas = listar_despesas_unificadas(
            args=args,
            politico_id=politico_id,
        )
        inicio = (page - 1) * per_page
        itens = todas[inicio:inicio + per_page]
        return envelope(
            itens,
            len(todas),
            page,
            per_page,
            resumo_financeiro=resumo_financeiro(todas),
        )

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
    else:
        raise ErroValidacao("parametro_invalido", "Tipo de rela??o desconhecido.")

    total = db.session.scalar(select(func.count()).select_from(base.subquery()))
    itens = db.session.scalars(
        base.order_by(ordem)
        .limit(per_page)
        .offset((page - 1) * per_page)
    ).all()

    return envelope(
        [serial(item) for item in itens],
        total,
        page,
        per_page,
    )
