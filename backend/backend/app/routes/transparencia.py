from flask import Blueprint, jsonify, request

from app.services import transparencia as svc

transparencia_bp = Blueprint("transparencia", __name__)


@transparencia_bp.get("/transparencia")
def panorama():
    return jsonify(svc.panorama())


@transparencia_bp.get("/transparencia/despesas")
def despesas():
    return jsonify(svc.listar_despesas(request.args))


@transparencia_bp.get("/transparencia/filtros")
def filtros():
    return jsonify(svc.listar_filtros())
