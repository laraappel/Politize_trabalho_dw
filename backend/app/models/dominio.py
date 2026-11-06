"""Mandatos, projetos, votações e despesas vinculados a políticos."""
from app.extensions import db


class Mandato(db.Model):
    __tablename__ = "mandatos"

    id = db.Column(db.BigInteger, primary_key=True)
    politico_id = db.Column(db.BigInteger, db.ForeignKey("politicos.id", ondelete="CASCADE"), nullable=False)
    cargo = db.Column(db.String(80), nullable=False)
    esfera = db.Column(db.String(20), nullable=False)
    uf = db.Column(db.String(2))
    municipio = db.Column(db.String(120))
    partido = db.Column(db.String(20))
    legislatura = db.Column(db.String(40))
    inicio = db.Column(db.Date, nullable=False)
    fim = db.Column(db.Date)
    origem_dados = db.Column(db.String(20), nullable=False, default="demonstracao")
    fonte_nome = db.Column(db.String(200))
    fonte_url = db.Column(db.Text)

    politico = db.relationship("Politico", back_populates="mandatos")


class Projeto(db.Model):
    __tablename__ = "projetos"

    id = db.Column(db.BigInteger, primary_key=True)
    politico_id = db.Column(db.BigInteger, db.ForeignKey("politicos.id", ondelete="CASCADE"), nullable=False)
    casa = db.Column(db.String(30), nullable=False)
    numero = db.Column(db.Integer)
    ano = db.Column(db.Integer)
    ementa = db.Column(db.Text)
    situacao = db.Column(db.String(40))
    data_apresentacao = db.Column(db.Date)
    url_oficial = db.Column(db.Text)
    origem_dados = db.Column(db.String(20), nullable=False, default="demonstracao")
    fonte_nome = db.Column(db.String(200))
    fonte_url = db.Column(db.Text)

    politico = db.relationship("Politico", back_populates="projetos")
    votacoes = db.relationship("Votacao", back_populates="projeto")


class Votacao(db.Model):
    __tablename__ = "votacoes"

    id = db.Column(db.BigInteger, primary_key=True)
    politico_id = db.Column(db.BigInteger, db.ForeignKey("politicos.id", ondelete="CASCADE"), nullable=False)
    projeto_id = db.Column(db.BigInteger, db.ForeignKey("projetos.id", ondelete="SET NULL"))
    identificador_externo = db.Column(db.String(80), nullable=False)
    casa = db.Column(db.String(30), nullable=False)
    data_votacao = db.Column(db.Date)
    ementa = db.Column(db.Text)
    voto = db.Column(db.String(20))
    url_oficial = db.Column(db.Text)
    origem_dados = db.Column(db.String(20), nullable=False, default="demonstracao")
    fonte_nome = db.Column(db.String(200))
    fonte_url = db.Column(db.Text)

    politico = db.relationship("Politico", back_populates="votacoes")
    projeto = db.relationship("Projeto", back_populates="votacoes")


class Despesa(db.Model):
    __tablename__ = "despesas"

    id = db.Column(db.BigInteger, primary_key=True)
    politico_id = db.Column(db.BigInteger, db.ForeignKey("politicos.id", ondelete="CASCADE"), nullable=False)
    categoria = db.Column(db.String(80), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    valor = db.Column(db.Numeric(14, 2))
    periodo_inicio = db.Column(db.Date, nullable=False)
    periodo_fim = db.Column(db.Date, nullable=False)
    esfera = db.Column(db.String(20))
    origem_dados = db.Column(db.String(20), nullable=False, default="demonstracao")
    fonte_nome = db.Column(db.String(200))
    fonte_url = db.Column(db.Text)

    politico = db.relationship("Politico", back_populates="despesas")
