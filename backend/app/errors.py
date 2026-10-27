from flask import jsonify


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "requisicao_invalida", "message": str(error)}), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify(
            {
                "error": "nao_encontrado",
                "message": "O recurso solicitado nao existe.",
            }
        ), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify(
            {
                "error": "metodo_nao_permitido",
                "message": "O metodo HTTP nao e permitido para esta rota.",
            }
        ), 405

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify(
            {
                "error": "erro_interno",
                "message": "Ocorreu um erro interno no servidor.",
            }
        ), 500
