from flask import Flask
from flask_cors import CORS

from app.config import Config
from app.errors import register_error_handlers
from app.extensions import db
from app.routes import register_blueprints


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    CORS(app, origins=app.config["FRONTEND_ORIGIN"], supports_credentials=False)

    register_blueprints(app)
    register_error_handlers(app)

    return app
