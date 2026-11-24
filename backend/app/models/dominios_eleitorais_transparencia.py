"""Entidades públicas para candidaturas e transparência patrimonial."""
from app.extensions import db


class Candidatura(db.Model):
    __tablename__ = "candidaturas"

    id = db.Column(db.BigInteger, primary_key=True)
    politico_id = db.Column(db.BigInteger, db.ForeignKey("politicos.id", ondelete="CASCADE"), nullable=False)
    partido_id = db.Column(db.BigInteger, db.ForeignKey("partidos.id", ondelete="RESTRICT"))
    ano = db.Column(db.Integer, nullable=False)
    cargo = db.Column(db.String(64), nullable=False)
    uf = db.Column(db.String(2))
    municipio = db.Column(db.String(120))
    sigla_partido = db.Column(db.String(32))
    nome_urna = db.Column(db.String(200))
    numero_candidatura = db.Column(db.String(16))
    resultado = db.Column(db.String(32))
    votos = db.Column(db.Integer)
    origem_dados = db.Column(db.String(20), nullable=False, default="demonstracao")
    fonte_nome = db.Column(db.String(200))
    fonte_url = db.Column(db.Text)
    atualizado_em = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    politico = db.relationship("Politico", foreign_keys=[politico_id])
    partido = db.relationship("Partido", foreign_keys=[partido_id])
    propostas = db.relationship("PropostaCampanha", back_populates="candidatura", cascade="all, delete-orphan")
    patrimonio = db.relationship("PatrimonioDeclarado", back_populates="candidatura")


class PropostaCampanha(db.Model):
    __tablename__ = "propostas_campanha"

    id = db.Column(db.BigInteger, primary_key=True)
    candidatura_id = db.Column(db.BigInteger, db.ForeignKey("candidaturas.id", ondelete="CASCADE"), nullable=False)
    titulo = db.Column(db.String(255), nullable=False)
    descricao = db.Column(db.Text)
    tema = db.Column(db.String(64))
    origem_dados = db.Column(db.String(20), nullable=False, default="demonstracao")
    fonte_nome = db.Column(db.String(200))
    fonte_url = db.Column(db.Text)
    atualizado_em = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    candidatura = db.relationship("Candidatura", back_populates="propostas")


class ProjetoCoautoria(db.Model):
    __tablename__ = "projeto_coautorias"

    id = db.Column(db.BigInteger, primary_key=True)
    projeto_id = db.Column(db.BigInteger, db.ForeignKey("projetos.id", ondelete="CASCADE"), nullable=False)
    politico_id = db.Column(db.BigInteger, db.ForeignKey("politicos.id", ondelete="CASCADE"), nullable=False)
    papel = db.Column(db.String(16), nullable=False, default="coautor")
    origem_dados = db.Column(db.String(20), nullable=False, default="demonstracao")
    fonte_nome = db.Column(db.String(200))
    fonte_url = db.Column(db.Text)
    atualizado_em = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    projeto = db.relationship("Projeto", back_populates="coautorias", foreign_keys=[projeto_id])
    politico = db.relationship("Politico", foreign_keys=[politico_id])


class Remuneracao(db.Model):
    __tablename__ = "remuneracoes"

    id = db.Column(db.BigInteger, primary_key=True)
    politico_id = db.Column(db.BigInteger, db.ForeignKey("politicos.id", ondelete="CASCADE"), nullable=False)
    cargo = db.Column(db.String(120))
    periodo_inicio = db.Column(db.Date, nullable=False)
    periodo_fim = db.Column(db.Date, nullable=False)
    valor_bruto = db.Column(db.Numeric(14, 2))
    beneficios = db.Column(db.Numeric(14, 2))
    descontos = db.Column(db.Numeric(14, 2))
    valor_liquido = db.Column(db.Numeric(14, 2))
    origem_dados = db.Column(db.String(20), nullable=False, default="demonstracao")
    fonte_nome = db.Column(db.String(200))
    fonte_url = db.Column(db.Text)
    atualizado_em = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    politico = db.relationship("Politico", foreign_keys=[politico_id])


class PatrimonioDeclarado(db.Model):
    __tablename__ = "patrimonio_declarado"

    id = db.Column(db.BigInteger, primary_key=True)
    politico_id = db.Column(db.BigInteger, db.ForeignKey("politicos.id", ondelete="CASCADE"), nullable=False)
    candidatura_id = db.Column(db.BigInteger, db.ForeignKey("candidaturas.id", ondelete="SET NULL"))
    ano_referencia = db.Column(db.Integer, nullable=False)
    tipo = db.Column(db.String(80), nullable=False)
    descricao = db.Column(db.Text)
    valor = db.Column(db.Numeric(14, 2))
    localizacao = db.Column(db.String(255))
    origem_dados = db.Column(db.String(20), nullable=False, default="demonstracao")
    fonte_nome = db.Column(db.String(200))
    fonte_url = db.Column(db.Text)
    atualizado_em = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    politico = db.relationship("Politico", foreign_keys=[politico_id])
    candidatura = db.relationship("Candidatura", back_populates="patrimonio")
