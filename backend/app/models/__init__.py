# Modelos SQLAlchemy do domínio ativo.
# DataSyncLog (Câmara) usa a tabela data_sync_logs.
# DataSourceSyncLog (fontes genéricas) usa data_source_sync_logs.
# Os modelos eleitorais em inglês (politician, party, candidacy, legislative,
# political_term) não são registrados: não têm migração, serviço nem rota.

from app.models.camara import (  # noqa: F401
    DataSyncLog,
    DespesaCamara,
    MandatoCamara,
    PartidoCamara,
    ProposicaoCamara,
)
from app.models.data_source import DataSource, DataSourceSyncLog  # noqa: F401
from app.models.dominio import Despesa, Mandato, Projeto, Votacao  # noqa: F401
from app.models.noticia import (  # noqa: F401
    ColetaNoticias,
    Noticia,
    NoticiaAtualizacao,
    NoticiaPolitico,
    PoliticoRef,
    Veiculo,
)
from app.models.partido import Partido  # noqa: F401
from app.models.politico import Politico  # noqa: F401