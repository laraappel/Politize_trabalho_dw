from app.routes.health import health_bp
from app.routes.noticias import noticias_bp


def register_blueprints(app):
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(noticias_bp, url_prefix="/api")
