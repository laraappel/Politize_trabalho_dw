# Modelos SQLAlchemy por domínio.

from app.models.data_source import DataSource, DataSourceSyncLog  # noqa: F401
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

from app.models.camara import (  # noqa: F401
    DataSyncLog,
    DespesaCamara,
    HistoricoCamara,
    MandatoCamara,
    PartidoCamara,
    ProposicaoCamara,
)

from app.models.politico import Politico  # noqa: F401
from app.models.dominios_eleitorais_transparencia import (  # noqa: F401
    Candidatura,
    PatrimonioDeclarado,
    ProjetoCoautoria,
    PropostaCampanha,
    Remuneracao,
)

from app.models.cargo_eletivo import CargoEletivo  # noqa: F401