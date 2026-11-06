from flask import Blueprint, jsonify, request

from app.services.noticias import consulta
from app.services.noticias.consulta import ErroValidacao

noticias_bp = Blueprint("noticias", __name__)


@noticias_bp.errorhandler(ErroValidacao)
def _erro_validacao(exc):
    return jsonify({"error": exc.codigo, "message": exc.mensagem}), exc.http


def _exigir_admin():
    token = request.headers.get("X-Admin-Token")
    import os

    if not os.getenv("ADMIN_TOKEN"):
        raise ErroValidacao("admin_desabilitado", "Operações editoriais estão desabilitadas (ADMIN_TOKEN não definido).", 403)
    if not consulta.admin_autorizado(token):
        raise ErroValidacao("nao_autorizado", "Token administrativo ausente ou inválido.", 401)


def _corpo():
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        raise ErroValidacao("requisicao_invalida", "Envie um corpo JSON (objeto).")
    return dados


# ------------------------------ leitura pública ------------------------------
@noticias_bp.get("/noticias")
def listar_noticias():
    return jsonify(consulta.listar_noticias(consulta.parse_filtros(request.args)))


@noticias_bp.get("/noticias/filtros")
def filtros():
    return jsonify(consulta.listar_filtros())


@noticias_bp.get("/noticias/<int:noticia_id>")
def detalhe(noticia_id):
    dados = consulta.obter_noticia(noticia_id)
    if dados is None:
        raise ErroValidacao("nao_encontrado", "O recurso solicitado nao existe.", 404)
    return jsonify(dados)


@noticias_bp.get("/veiculos")
def veiculos():
    return jsonify({"items": consulta.listar_veiculos()})


@noticias_bp.get("/politicos/<int:politico_id>/noticias")
def noticias_do_politico(politico_id):
    args = request.args.to_dict()
    args["politico"] = str(politico_id)
    if not consulta.politico_existe(politico_id):
        raise ErroValidacao("nao_encontrado", "Político não encontrado.", 404)
    return jsonify(consulta.listar_noticias(consulta.parse_filtros(args)))


# --------------------- operações editoriais (token admin) --------------------
@noticias_bp.get("/noticias/revisao")
def pendentes():
    _exigir_admin()
    f = consulta.parse_filtros(request.args)
    return jsonify(consulta.listar_pendentes(f.page, f.per_page))


@noticias_bp.post("/noticias/<int:noticia_id>/atualizacoes")
def nova_atualizacao(noticia_id):
    _exigir_admin()
    return jsonify(consulta.adicionar_atualizacao(noticia_id, _corpo())), 201


@noticias_bp.post("/noticias/<int:noticia_id>/politicos/<int:politico_id>/revisao")
def revisar(noticia_id, politico_id):
    _exigir_admin()
    return jsonify(consulta.revisar_associacao(noticia_id, politico_id, _corpo()))


@noticias_bp.patch("/noticias/<int:noticia_id>/natureza")
def natureza(noticia_id):
    _exigir_admin()
    return jsonify(consulta.reclassificar_natureza(noticia_id, _corpo()))
