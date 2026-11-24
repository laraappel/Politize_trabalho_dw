from flask import Blueprint, jsonify, current_app
from sqlalchemy import text

from app.extensions import db

health_bp = Blueprint("health", __name__)


def check_database():
    try:
        db.session.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception:
        current_app.logger.exception(
            "ERRO AO CONECTAR AO BANCO DE DADOS"
        )
        db.session.rollback()
        return {"status": "unavailable"}

@health_bp.get("/health")
def health():
    database = check_database()
    payload = {
        "status": "ok" if database["status"] == "ok" else "degraded",
        "api": {"status": "ok"},
        "database": database,
        "service": "voto-transparente-api",
    }
    http_status = 200 if payload["status"] == "ok" else 503
    return jsonify(payload), http_status
