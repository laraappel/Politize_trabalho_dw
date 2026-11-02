"""Modelos do módulo de notícias. Tabelas definidas em database/migrations/002_noticias.sql."""
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy import Text

from app.extensions import db


class PoliticoRef(db.Model):
    """Visão mínima de `politicos`, usada apenas para vincular notícias.

    O módulo de políticos pode substituir/estender este modelo; o módulo de
    notícias só lê id, nomes, cargo, partido e identificadores oficiais.
    """

    __tablename__ = "politicos"

    id = db.Column(db.BigInteger, primary_key=True)
    nome_completo = db.Column(db.String(200), nullable=False)
    nome_urna = db.Column(db.String(200))
    apelidos = db.Column(ARRAY(Text), nullable=False, default=list)
    cargo = db.Column(db.String(80))
    uf = db.Column(db.String(2))
    partido = db.Column(db.String(20))
    id_camara = db.Column(db.Integer, unique=True)
    id_senado = db.Column(db.Integer, unique=True)
    origem_dados = db.Column(db.String(80))
    coletado_em = db.Column(db.DateTime(timezone=True))
    atualizado_em = db.Column(db.DateTime(timezone=True))
    dados_camara = db.Column(JSONB)

    @property
    def nome_exibicao(self):
        return self.nome_urna or self.nome_completo


class Veiculo(db.Model):
    __tablename__ = "veiculos"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(60), nullable=False, unique=True)
    nome = db.Column(db.String(120), nullable=False)
    dominio = db.Column(db.String(120), nullable=False)
    tipo = db.Column(db.String(30), nullable=False, default="imprensa")
    coleta_autorizada = db.Column(db.Boolean, nullable=False, default=False)
    permite_resumo = db.Column(db.Boolean, nullable=False, default=False)
    base_autorizacao = db.Column(db.Text, nullable=False)
    url_termos = db.Column(db.Text)
    ultima_coleta_em = db.Column(db.DateTime(timezone=True))


class Noticia(db.Model):
    __tablename__ = "noticias"

    id = db.Column(db.BigInteger, primary_key=True)
    veiculo_id = db.Column(db.Integer, db.ForeignKey("veiculos.id"), nullable=False)
    url_original = db.Column(db.Text, nullable=False)
    url_canonica = db.Column(db.Text, nullable=False, unique=True)
    guid_origem = db.Column(db.Text)
    chave_dedup = db.Column(db.String(64), nullable=False, unique=True)
    titulo_original = db.Column(db.Text, nullable=False)
    resumo = db.Column(db.String(400))
    publicado_em = db.Column(db.DateTime(timezone=True))
    assunto_slug = db.Column(db.String(80))
    assunto_nome = db.Column(db.String(120))
    natureza = db.Column(db.String(30), nullable=False, default="nao_classificado")
    natureza_origem = db.Column(db.String(20), nullable=False, default="heuristica")
    coletado_em = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    atualizado_em = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    veiculo = db.relationship("Veiculo")
    associacoes = db.relationship(
        "NoticiaPolitico", back_populates="noticia", cascade="all, delete-orphan"
    )
    atualizacoes = db.relationship(
        "NoticiaAtualizacao",
        foreign_keys="NoticiaAtualizacao.noticia_id",
        order_by="NoticiaAtualizacao.criado_em",
        cascade="all, delete-orphan",
    )


class NoticiaPolitico(db.Model):
    __tablename__ = "noticia_politicos"

    noticia_id = db.Column(
        db.BigInteger, db.ForeignKey("noticias.id", ondelete="CASCADE"), primary_key=True
    )
    politico_id = db.Column(
        db.BigInteger, db.ForeignKey("politicos.id", ondelete="CASCADE"), primary_key=True
    )
    status = db.Column(db.String(20), nullable=False)
    grau_confirmacao = db.Column(db.String(10), nullable=False)
    metodo = db.Column(db.String(40), nullable=False)
    origem = db.Column(db.String(12), nullable=False, default="automatica")
    evidencias = db.Column(JSONB, nullable=False, default=list)
    revisado_por = db.Column(db.String(80))
    revisado_em = db.Column(db.DateTime(timezone=True))
    criado_em = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    noticia = db.relationship("Noticia", back_populates="associacoes")
    politico = db.relationship("PoliticoRef")


class NoticiaAtualizacao(db.Model):
    __tablename__ = "noticia_atualizacoes"

    id = db.Column(db.BigInteger, primary_key=True)
    noticia_id = db.Column(
        db.BigInteger, db.ForeignKey("noticias.id", ondelete="CASCADE"), nullable=False
    )
    tipo = db.Column(db.String(30), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    url_referencia = db.Column(db.Text)
    noticia_relacionada_id = db.Column(
        db.BigInteger, db.ForeignKey("noticias.id", ondelete="SET NULL")
    )
    criado_por = db.Column(db.String(80), nullable=False, default="sistema")
    criado_em = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    noticia_relacionada = db.relationship("Noticia", foreign_keys=[noticia_relacionada_id])


class ColetaNoticias(db.Model):
    __tablename__ = "coletas_noticias"

    id = db.Column(db.BigInteger, primary_key=True)
    veiculo_id = db.Column(db.Integer, db.ForeignKey("veiculos.id"), nullable=False)
    iniciada_em = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    finalizada_em = db.Column(db.DateTime(timezone=True))
    status = db.Column(db.String(20), nullable=False, default="em_andamento")
    itens_lidos = db.Column(db.Integer, nullable=False, default=0)
    itens_novos = db.Column(db.Integer, nullable=False, default=0)
    itens_atualizados = db.Column(db.Integer, nullable=False, default=0)
    itens_descartados = db.Column(db.Integer, nullable=False, default=0)
    mensagem = db.Column(db.Text)
