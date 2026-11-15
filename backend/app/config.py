import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
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
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", os.getenv("DATABASE_URL"))
