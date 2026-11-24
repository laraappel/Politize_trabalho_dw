import os


def _database_url(variable="DATABASE_URL"):
    url = os.getenv(variable)
    if not url:
        return None
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url.removeprefix("postgres://")
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url.removeprefix("postgresql://")
    return url


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    if os.getenv("VERCEL") == "1":
        SQLALCHEMY_ENGINE_OPTIONS.update(
            {"pool_size": 1, "max_overflow": 0, "pool_recycle": 300}
        )
    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
    JSON_SORT_KEYS = False
    # Módulo de notícias: ver docs/NOTICIAS.md
    ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")
    CAMARA_USER_AGENT = os.getenv(
        "CAMARA_USER_AGENT",
        "VotoTransparente/0.1 (projeto academico; dados abertos da Camara)",
    )
    CAMARA_HTTP_TIMEOUT = int(os.getenv("CAMARA_HTTP_TIMEOUT", "20"))
    CAMARA_INTERVALO_SEGUNDOS = float(os.getenv("CAMARA_INTERVALO_SEGUNDOS", "0.4"))
    CAMARA_TENTATIVAS = int(os.getenv("CAMARA_TENTATIVAS", "3"))
    CAMARA_ITENS_POR_PAGINA = int(os.getenv("CAMARA_ITENS_POR_PAGINA", "100"))


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = _database_url("TEST_DATABASE_URL") or _database_url()
