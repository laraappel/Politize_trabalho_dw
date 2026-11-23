"""Partidos com o identificador oficial da Câmara dos Deputados."""
from app.extensions import db


class Partido(db.Model):
    __tablename__ = "partidos"

    id = db.Column(db.BigInteger, primary_key=True)
    id_camara = db.Column(db.Integer, nullable=False, unique=True)
    sigla = db.Column(db.String(30), nullable=False)
    nome = db.Column(db.String(200), nullable=False)
    uri = db.Column(db.Text)
    origem_dados = db.Column(db.String(20), nullable=False, default="oficial")
    fonte_nome = db.Column(db.String(200), nullable=False)
    fonte_url = db.Column(db.Text, nullable=False)
    coletado_em = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    atualizado_em = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
