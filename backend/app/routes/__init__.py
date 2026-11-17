from app.routes.camara import camara_bp
from app.routes.health import health_bp
from app.routes.noticias import noticias_bp
<<<<<<< HEAD
from app.routes.camara import camara_bp
=======
from app.routes.politicos import politicos_bp
from app.routes.transparencia import transparencia_bp
>>>>>>> 5ebe20d0034f953c5898dc87e9dc700a437290e5


def register_blueprints(app):
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(politicos_bp, url_prefix="/api")
    app.register_blueprint(transparencia_bp, url_prefix="/api")
    app.register_blueprint(noticias_bp, url_prefix="/api")
    app.register_blueprint(camara_bp, url_prefix="/api")
