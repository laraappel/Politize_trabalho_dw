# Modelos SQLAlchemy por dominio.
from app.models.data_source import DataSource, DataSyncLog  # noqa: F401
from app.models.dominio import Despesa, Mandato, Projeto, Votacao  # noqa: F401
from app.models.partido import Partido  # noqa: F401
from app.models.noticia import (  # noqa: F401
    ColetaNoticias,
    Noticia,
    NoticiaAtualizacao,
    NoticiaPolitico,
    PoliticoRef,
    Veiculo,
)
from app.models.politico import Politico  # noqa: F401
