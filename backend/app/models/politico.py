"""Cadastro de políticos compartilhado por todos os módulos."""
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

from app.extensions import db


class Politico(db.Model):
    __tablename__ = "politicos"

    id = db.Column(db.BigInteger, primary_key=True)
    slug = db.Column(db.String(80), unique=True)
    nome_completo = db.Column(db.String(200), nullable=False)
    nome_urna = db.Column(db.String(200))
    apelidos = db.Column(ARRAY(Text), nullable=False, default=list)
    cargo = db.Column(db.String(80))
    uf = db.Column(db.String(2))
    municipio = db.Column(db.String(120))
    partido = db.Column(db.String(20))
    id_camara = db.Column(db.Integer, unique=True)
    id_senado = db.Column(db.Integer, unique=True)
    origem_dados = db.Column(db.String(80), nullable=False, default="demonstracao")
    fonte_nome = db.Column(db.String(200))
    fonte_url = db.Column(db.Text)
    criado_em = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    atualizado_em = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    coletado_em = db.Column(db.DateTime(timezone=True))
    dados_camara = db.Column(JSONB)

    mandatos = db.relationship("Mandato", back_populates="politico", order_by="Mandato.inicio.desc()")
    projetos = db.relationship("Projeto", back_populates="politico", order_by="Projeto.data_apresentacao.desc()")
    votacoes = db.relationship("Votacao", back_populates="politico", order_by="Votacao.data_votacao.desc()")
    despesas = db.relationship("Despesa", back_populates="politico", order_by="Despesa.periodo_inicio.desc()")

    @property
    def nome_exibicao(self):
        return self.nome_urna or self.nome_completo

    @property
    def demonstracao(self):
        return self.origem_dados == "demonstracao"
