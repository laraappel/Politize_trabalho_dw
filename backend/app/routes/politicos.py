from flask import Blueprint, jsonify, request

from app.errors import ErroValidacao
from app.services import politicos as svc

politicos_bp = Blueprint("politicos", __name__)


@politicos_bp.get("/politicos")
def listar():
    return jsonify(svc.listar(request.args))


@politicos_bp.get("/politicos/filtros")
def filtros():
    return jsonify(svc.listar_filtros())


@politicos_bp.get("/politicos/<int:politico_id>")
def detalhe(politico_id):
    dados = svc.detalhe(politico_id)
    if dados is None:
        raise ErroValidacao("nao_encontrado", "Político não encontrado.", 404)
    return jsonify(dados)


@politicos_bp.get("/politicos/<int:politico_id>/mandatos")
def mandatos(politico_id):
    return jsonify(svc.listar_relacionados(politico_id, request.args, "mandatos"))


@politicos_bp.get("/politicos/<int:politico_id>/projetos")
def projetos(politico_id):
    return jsonify(svc.listar_relacionados(politico_id, request.args, "projetos"))


@politicos_bp.get("/politicos/<int:politico_id>/votacoes")
def votacoes(politico_id):
    return jsonify(svc.listar_relacionados(politico_id, request.args, "votacoes"))


@politicos_bp.get("/politicos/<int:politico_id>/despesas")
def despesas(politico_id):
    return jsonify(svc.listar_relacionados(politico_id, request.args, "despesas"))
