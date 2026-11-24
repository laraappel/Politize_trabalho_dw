from app.extensions import db


class CargoEletivo(db.Model):
    __tablename__ = "cargos_eletivos"

    id = db.Column(db.BigInteger, primary_key=True)
    politico_id = db.Column(db.BigInteger, db.ForeignKey("politicos.id", ondelete="CASCADE"))
    cargo = db.Column(db.String(64), nullable=False)
    esfera = db.Column(db.String(20), nullable=False)
    uf = db.Column(db.String(2))
    municipio = db.Column(db.String(120))
    partido = db.Column(db.String(32))
    ano_eleicao = db.Column(db.Integer)
    ano_inicio = db.Column(db.Integer)
    ano_fim = db.Column(db.Integer)
    situacao = db.Column(db.String(64), nullable=False, default="em_exercicio")
    identificador_externo = db.Column(db.String(128))
    origem = db.Column(db.String(80), nullable=False)
    fonte_nome = db.Column(db.String(200), nullable=False)
    fonte_url = db.Column(db.Text, nullable=False)
    dados_origem = db.Column(db.JSON)
    coletado_em = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    atualizado_em = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    politico = db.relationship("Politico")
