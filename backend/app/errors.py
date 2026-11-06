from flask import jsonify


class ErroValidacao(Exception):
    """Erro de entrada ou regra de negócio com código estável para a API."""

    def __init__(self, codigo: str, mensagem: str, http: int = 400):
        super().__init__(mensagem)
        self.codigo = codigo
        self.mensagem = mensagem
        self.http = http


def register_error_handlers(app):
    @app.errorhandler(ErroValidacao)
    def validacao(error):
        return jsonify({"error": error.codigo, "message": error.mensagem}), error.http

    @app.errorhandler(400)
    def bad_request(_error):
        return jsonify(
            {
                "error": "requisicao_invalida",
                "message": "A requisicao enviada e invalida.",
            }
        ), 400

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify(
            {
                "error": "nao_encontrado",
                "message": "O recurso solicitado nao existe.",
            }
        ), 404

    @app.errorhandler(405)
    def method_not_allowed(_error):
        return jsonify(
            {
                "error": "metodo_nao_permitido",
                "message": "O metodo HTTP nao e permitido para esta rota.",
            }
        ), 405

    @app.errorhandler(500)
    def internal_error(_error):
        return jsonify(
            {
                "error": "erro_interno",
                "message": "Ocorreu um erro interno no servidor.",
            }
        ), 500
