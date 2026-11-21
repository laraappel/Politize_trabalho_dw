
"""Consultas públicas aos dados normalizados importados da Câmara."""
from flask import Blueprint, jsonify, request
from sqlalchemy import or_, select

from app.extensions import db
from app.models.noticia import PoliticoRef
from app.models.camara import (
    DataSyncLog,
    DespesaCamara,
    HistoricoCamara,
    MandatoCamara,
    PartidoCamara,
    ProposicaoCamara,
)

camara_bp = Blueprint("camara", __name__)


def _paginacao():
    try:
        pagina = max(1, int(request.args.get("pagina", 1)))
        limite = min(100, max(1, int(request.args.get("limite", 20))))
    except ValueError:
        return None, None, (
            jsonify({
                "error": "parametro_invalido",
                "message": "pagina e limite devem ser números inteiros.",
            }),
            400,
        )
    return pagina, limite, None


def _iso(valor):
    return valor.isoformat() if valor is not None else None


def _politico_por_camara(id_camara):
    return db.session.execute(
        select(PoliticoRef).where(PoliticoRef.id_camara == id_camara)
    ).scalar_one_or_none()


def _nao_encontrado():
    return jsonify({
        "error": "deputado_nao_encontrado",
        "message": "Deputado não encontrado na base importada.",
    }), 404


def _despesa_json(d, politico=None):
    dados = {
        "id_camara": d.id_deputado_camara,
        "id_documento": d.id_documento,
        "ano": d.ano,
        "mes": d.mes,
        "tipo_despesa": d.tipo_despesa,
        "tipo_documento": d.tipo_documento,
        "data_documento": _iso(d.data_documento),
        "fornecedor": d.fornecedor,
        "cnpj_cpf_fornecedor": d.cnpj_cpf_fornecedor,
        "valor_documento": (
            str(d.valor_documento) if d.valor_documento is not None else None
        ),
        "valor_liquido": (
            str(d.valor_liquido) if d.valor_liquido is not None else None
        ),
        "url_documento": d.url_documento,
        "origem": d.origem,
        "coletado_em": _iso(d.coletado_em),
        "atualizado_em": _iso(d.atualizado_em),
    }
    if politico is not None:
        dados["politico"] = {
            "id": politico.id,
            "nome": politico.nome_exibicao,
            "partido": politico.partido,
            "uf": politico.uf,
        }
    return dados


def _deputado_json(p):
    return {
        "id": p.id,
        "id_camara": p.id_camara,
        "nome": p.nome_exibicao,
        "nome_completo": p.nome_completo,
        "cargo": p.cargo,
        "uf": p.uf,
        "partido": p.partido,
        "origem": p.origem_dados,
        "criado_em": _iso(p.criado_em),
        "atualizado_em": _iso(p.atualizado_em),
    }


@camara_bp.get("/deputados")
def listar_deputados():
    pagina, limite, erro = _paginacao()
    if erro:
        return erro

    consulta = select(PoliticoRef).where(PoliticoRef.id_camara.is_not(None))
    uf = request.args.get("uf")
    partido = request.args.get("partido")

    if uf:
        consulta = consulta.where(PoliticoRef.uf == uf.upper())
    if partido:
        consulta = consulta.where(PoliticoRef.partido == partido.upper())

    total = db.session.scalar(
        select(db.func.count()).select_from(consulta.subquery())
    )

    registros = db.session.execute(
        consulta.order_by(PoliticoRef.nome_completo)
        .offset((pagina - 1) * limite)
        .limit(limite)
    ).scalars().all()

    return jsonify({
        "dados": [_deputado_json(p) for p in registros],
        "paginacao": {
            "pagina": pagina,
            "limite": limite,
            "total": total,
        },
    })


@camara_bp.get("/deputados/<int:id_camara>")
def obter_deputado(id_camara):
    politico = _politico_por_camara(id_camara)
    if politico is None:
        return _nao_encontrado()

    mandatos = db.session.execute(
        select(MandatoCamara)
        .where(
            MandatoCamara.id_deputado_camara == id_camara,
            or_(
                MandatoCamara.data_inicio.is_not(None),
                MandatoCamara.data_fim.is_not(None),
            ),
        )
        .order_by(MandatoCamara.data_inicio.desc())
    ).scalars().all()

    historico = db.session.execute(
        select(HistoricoCamara)
        .where(HistoricoCamara.id_deputado_camara == id_camara)
        .order_by(
            HistoricoCamara.data_hora.desc().nulls_last(),
            HistoricoCamara.id.desc(),
        )
    ).scalars().all()

    dados = _deputado_json(politico)
    dados["mandatos"] = [{
        "legislatura": m.id_legislatura,
        "inicio": _iso(m.data_inicio),
        "fim": _iso(m.data_fim),
        "partido": m.partido_sigla,
        "uf": m.uf,
        "situacao": m.situacao,
        "origem": m.origem,
        "coletado_em": _iso(m.coletado_em),
        "atualizado_em": _iso(m.atualizado_em),
    } for m in mandatos]

    dados["historico"] = [{
        "legislatura": h.id_legislatura,
        "nome": h.nome,
        "nome_eleitoral": h.nome_eleitoral,
        "partido": h.sigla_partido,
        "uf": h.sigla_uf,
        "email": h.email,
        "url_foto": h.url_foto,
        "data_hora": _iso(h.data_hora),
        "situacao": h.situacao,
        "condicao_eleitoral": h.condicao_eleitoral,
        "descricao_status": h.descricao_status,
        "uri": h.uri_origem,
        "origem": h.origem,
        "coletado_em": _iso(h.coletado_em),
    } for h in historico]

    return jsonify({"dados": dados})


@camara_bp.get("/deputados/<int:id_camara>/despesas")
def despesas_deputado(id_camara):
    pagina, limite, erro = _paginacao()
    if erro:
        return erro

    consulta = select(DespesaCamara).where(
        DespesaCamara.id_deputado_camara == id_camara
    )

    try:
        if request.args.get("ano"):
            consulta = consulta.where(
                DespesaCamara.ano == int(request.args["ano"])
            )
        if request.args.get("mes"):
            consulta = consulta.where(
                DespesaCamara.mes == int(request.args["mes"])
            )
    except ValueError:
        return jsonify({
            "error": "parametro_invalido",
            "message": "ano e mes devem ser números inteiros.",
        }), 400

    if request.args.get("tipo_despesa"):
        consulta = consulta.where(
            DespesaCamara.tipo_despesa == request.args["tipo_despesa"]
        )

    total = db.session.scalar(
        select(db.func.count()).select_from(consulta.subquery())
    )

    registros = db.session.execute(
        consulta.order_by(
            DespesaCamara.ano.desc(),
            DespesaCamara.mes.desc(),
            DespesaCamara.data_documento.desc(),
        )
        .offset((pagina - 1) * limite)
        .limit(limite)
    ).scalars().all()

    return jsonify({
        "dados": [{
            "id_camara": d.id_deputado_camara,
            "id_documento": d.id_documento,
            "ano": d.ano,
            "mes": d.mes,
            "tipo_despesa": d.tipo_despesa,
            "tipo_documento": d.tipo_documento,
            "data_documento": _iso(d.data_documento),
            "fornecedor": d.fornecedor,
            "cnpj_cpf_fornecedor": d.cnpj_cpf_fornecedor,
            "valor_documento": (
                str(d.valor_documento)
                if d.valor_documento is not None else None
            ),
            "valor_liquido": (
                str(d.valor_liquido)
                if d.valor_liquido is not None else None
            ),
            "url_documento": d.url_documento,
            "origem": d.origem,
            "coletado_em": _iso(d.coletado_em),
            "atualizado_em": _iso(d.atualizado_em),
        } for d in registros],
        "contexto": {
            "ano": request.args.get("ano"),
            "mes": request.args.get("mes"),
            "tipo_despesa": request.args.get("tipo_despesa"),
        },
        "paginacao": {
            "pagina": pagina,
            "limite": limite,
            "total": total,
        },
    })


@camara_bp.get("/proposicoes")
def listar_proposicoes():
    pagina, limite, erro = _paginacao()
    if erro:
        return erro

    consulta = select(ProposicaoCamara)

    try:
        if request.args.get("ano"):
            consulta = consulta.where(
                ProposicaoCamara.ano == int(request.args["ano"])
            )
    except ValueError:
        return jsonify({
            "error": "parametro_invalido",
            "message": "ano deve ser um número inteiro.",
        }), 400

    if request.args.get("sigla_tipo"):
        consulta = consulta.where(
            ProposicaoCamara.sigla_tipo == request.args["sigla_tipo"].upper()
        )

    total = db.session.scalar(
        select(db.func.count()).select_from(consulta.subquery())
    )

    registros = db.session.execute(
        consulta.order_by(
            ProposicaoCamara.ano.desc(),
            ProposicaoCamara.numero.desc(),
        )
        .offset((pagina - 1) * limite)
        .limit(limite)
    ).scalars().all()

    return jsonify({
        "dados": [{
            "id_camara": p.id_proposicao_camara,
            "uri": p.uri_origem,
            "tipo": p.sigla_tipo,
            "numero": p.numero,
            "ano": p.ano,
            "ementa": p.ementa,
            "data_apresentacao": _iso(p.data_apresentacao),
            "status": p.status_descricao,
            "status_data_hora": _iso(p.status_data_hora),
            "origem": p.origem,
            "coletado_em": _iso(p.coletado_em),
            "atualizado_em": _iso(p.atualizado_em),
        } for p in registros],
        "paginacao": {
            "pagina": pagina,
            "limite": limite,
            "total": total,
        },
    })


@camara_bp.get("/partidos")
def listar_partidos():
    registros = db.session.execute(
        select(PartidoCamara).order_by(PartidoCamara.sigla)
    ).scalars().all()

    return jsonify({
        "dados": [{
            "id_camara": p.id_partido_camara,
            "sigla": p.sigla,
            "nome": p.nome,
            "uri": p.uri_origem,
            "origem": p.origem,
        } for p in registros],
    })


@camara_bp.get("/data-sync-logs")
def listar_logs_sincronizacao():
    pagina, limite, erro = _paginacao()
    if erro:
        return erro

    registros = db.session.execute(
        select(DataSyncLog)
        .order_by(DataSyncLog.iniciada_em.desc())
        .offset((pagina - 1) * limite)
        .limit(limite)
    ).scalars().all()

    return jsonify({
        "dados": [{
            "id": l.id,
            "fonte": l.fonte,
            "entidade": l.entidade,
            "operacao": l.operacao,
            "status": l.status,
            "iniciada_em": _iso(l.iniciada_em),
            "finalizada_em": _iso(l.finalizada_em),
            "registros_lidos": l.registros_lidos,
            "registros_novos": l.registros_novos,
            "registros_atualizados": l.registros_atualizados,
            "mensagem": l.mensagem,
        } for l in registros],
    })
