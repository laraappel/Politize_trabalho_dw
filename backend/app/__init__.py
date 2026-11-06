from flask import Flask
from flask_cors import CORS

from app.cli import register_cli
from app.config import Config
from app.errors import register_error_handlers
from app.extensions import db
from app.routes import register_blueprints


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    from app import models  # noqa: F401  — registra mapeamentos SQLAlchemy

    origens = [o.strip() for o in str(app.config["FRONTEND_ORIGIN"]).split(",") if o.strip()]
    CORS(app, origins=origens or ["http://localhost:3000"], supports_credentials=False)

    register_blueprints(app)
    register_cli(app)
    register_error_handlers(app)

    return app
