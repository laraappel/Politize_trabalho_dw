from flask import Blueprint, jsonify, request

from app.errors import ErroValidacao
from app.services import dominios_eleitorais as svc


eleitorais_bp = Blueprint("dominios_eleitorais", __name__)


@eleitorais_bp.get("/partidos-cadastrados")
def partidos():
    return jsonify(svc.listar_partidos(request.args))


@eleitorais_bp.get("/partidos-cadastrados/<int:partido_id>")
def partido(partido_id):
    dados = svc.detalhe_partido(partido_id)
    if dados is None:
        raise ErroValidacao("nao_encontrado", "Partido não encontrado.", 404)
    return jsonify(dados)


@eleitorais_bp.get("/politicos/<int:politico_id>/candidaturas")
def candidaturas(politico_id):
    return jsonify(svc.listar_candidaturas(politico_id, request.args))


@eleitorais_bp.get("/candidaturas/<int:candidatura_id>/propostas")
def propostas_candidatura(candidatura_id):
    return jsonify(svc.listar_propostas_candidatura(candidatura_id, request.args))


@eleitorais_bp.get("/projetos/<int:projeto_id>/coautorias")
def coautorias(projeto_id):
    return jsonify(svc.listar_coautorias_projeto(projeto_id, request.args))


@eleitorais_bp.get("/politicos/<int:politico_id>/remuneracoes")
def remuneracoes(politico_id):
    return jsonify(svc.listar_remuneracoes(politico_id, request.args))


@eleitorais_bp.get("/politicos/<int:politico_id>/patrimonio")
def patrimonio(politico_id):
    return jsonify(svc.listar_patrimonio(politico_id, request.args))
