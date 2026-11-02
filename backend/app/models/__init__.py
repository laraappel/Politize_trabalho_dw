# Modelos SQLAlchemy por domínio.
from app.models.noticia import (  # noqa: F401
    ColetaNoticias, Noticia, NoticiaAtualizacao, NoticiaPolitico, PoliticoRef, Veiculo,
)
from app.models.camara import (  # noqa: F401
    DataSyncLog, DespesaCamara, MandatoCamara, PartidoCamara, ProposicaoCamara,
)
