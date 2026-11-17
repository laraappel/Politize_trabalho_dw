<<<<<<< HEAD
# Modelos SQLAlchemy por domínio.
=======
# Modelos SQLAlchemy por dominio.
from app.models.data_source import DataSource, DataSyncLog  # noqa: F401
from app.models.dominio import Despesa, Mandato, Projeto, Votacao  # noqa: F401
from app.models.partido import Partido  # noqa: F401
>>>>>>> 5ebe20d0034f953c5898dc87e9dc700a437290e5
from app.models.noticia import (  # noqa: F401
    ColetaNoticias, Noticia, NoticiaAtualizacao, NoticiaPolitico, PoliticoRef, Veiculo,
)
from app.models.camara import (  # noqa: F401
    DataSyncLog, DespesaCamara, MandatoCamara, PartidoCamara, ProposicaoCamara,
)
from app.models.politico import Politico  # noqa: F401
