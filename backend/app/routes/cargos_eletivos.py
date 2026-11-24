from flask import Blueprint, jsonify, request

from app.services.cargos_eletivos import filtros_cargos, listar_cargos


cargos_eletivos_bp = Blueprint("cargos_eletivos", __name__)


@cargos_eletivos_bp.get("/cargos-eletivos")
def listar():
    return jsonify(listar_cargos(request.args))


@cargos_eletivos_bp.get("/cargos-eletivos/filtros")
def filtros():
    return jsonify(filtros_cargos())
