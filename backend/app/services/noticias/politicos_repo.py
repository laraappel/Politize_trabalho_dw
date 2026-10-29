"""Único ponto onde o módulo de notícias lê o cadastro de políticos.
Se o módulo de políticos mudar o schema, adapte apenas esta função."""
from app.extensions import db
from app.models.noticia import PoliticoRef
from app.services.noticias.associacao import PoliticoCadastro


def carregar_politicos() -> list[PoliticoCadastro]:
    linhas = db.session.execute(db.select(PoliticoRef)).scalars().all()
    return [
        PoliticoCadastro(
            id=p.id,
            nome_completo=p.nome_completo,
            nome_urna=p.nome_urna,
            apelidos=tuple(p.apelidos or ()),
            cargo=p.cargo,
            partido=p.partido,
            id_camara=p.id_camara,
            id_senado=p.id_senado,
        )
        for p in linhas
    ]
