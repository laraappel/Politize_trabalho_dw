# Modelos SQLAlchemy por dominio.
from app.models.dominio import Despesa, Mandato, Projeto, Votacao  # noqa: F401
from app.models.noticia import (  # noqa: F401
    ColetaNoticias,
    Noticia,
    NoticiaAtualizacao,
    NoticiaPolitico,
    PoliticoRef,
    Veiculo,
)
from app.models.politico import Politico  # noqa: F401
