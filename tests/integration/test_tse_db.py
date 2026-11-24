"""Importação oficial TSE e exposição dos resultados pela API."""
import io
import os
import zipfile

import pytest
from sqlalchemy import text

if not os.getenv("DATABASE_URL"):
    pytest.skip("DATABASE_URL não definido", allow_module_level=True)

from app import create_app
from app.extensions import db
from app.models.politico import Politico
from app.services.tse import sincronizar_tse

pytestmark = pytest.mark.integration
SLUG = "tse-2024-tse-integration-candidate"
CODIGO = "tse-integration-candidate"


def _arquivo_tse():
    conteudo = io.BytesIO()
    cabecalho = (
        "SQ_CANDIDATO;NR_CPF_CANDIDATO;NM_CANDIDATO;NM_URNA_CANDIDATO;"
        "DS_CARGO;DS_SIT_TOT_TURNO;SG_UF;NM_UE;SG_PARTIDO;NR_CANDIDATO\n"
    )
    linha = f"{CODIGO};;Candidata TSE Integração;Candidata Integração;PREFEITO;ELEITO;SC;Cidade Integração;PT;13\n"
    with zipfile.ZipFile(conteudo, "w") as arquivo:
        arquivo.writestr("consulta_cand_2024_SC.csv", (cabecalho + linha).encode("latin1"))
    return conteudo.getvalue()


class RespostaFalsa:
    content = _arquivo_tse()

    def raise_for_status(self):
        return None


def test_importa_candidato_e_expoe_ano_situacao_e_fonte():
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        try:
            resultado = sincronizar_tse([2024], baixar=lambda *args, **kwargs: RespostaFalsa())
            politico = db.session.scalar(db.select(Politico).where(Politico.slug == SLUG))
            assert resultado["eleitos"] == 1
            assert politico is not None
            politico_id = politico.id
            client = app.test_client()
            lista = client.get(
                "/api/cargos-eletivos?ano=2024&cargo=Prefeito&uf=SC&q=Candidata%20Integração"
            ).get_json()
            assert lista["total"] == 1
            assert lista["items"][0]["ano_eleicao"] == 2024
            assert lista["items"][0]["situacao"] == "ELEITO"
            candidatura = client.get(f"/api/politicos/{politico_id}/candidaturas").get_json()
            assert candidatura["items"][0]["ano"] == 2024
            assert candidatura["items"][0]["resultado"] == "ELEITO"
            assert candidatura["items"][0]["partido_sigla"] == "PT"
            assert candidatura["items"][0]["fonte"]["nome"] == "Tribunal Superior Eleitoral (TSE)"
        finally:
            db.session.execute(text("DELETE FROM cargos_eletivos WHERE origem='tse_2024' AND identificador_externo=:codigo"), {"codigo": CODIGO})
            db.session.execute(text("DELETE FROM candidaturas WHERE politico_id IN (SELECT id FROM politicos WHERE slug=:slug)"), {"slug": SLUG})
            db.session.execute(text("DELETE FROM politicos WHERE slug=:slug"), {"slug": SLUG})
            db.session.commit()
