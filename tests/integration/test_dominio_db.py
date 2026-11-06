"""Fluxos de políticos, despesas, importação idempotente e contratos da API."""
import os

import pytest
from sqlalchemy import text

if not os.getenv("DATABASE_URL"):
    pytest.skip("DATABASE_URL não definido", allow_module_level=True)

from app import create_app
from app.extensions import db
from app.models.politico import Politico
from app.services.importacao import importar_pacote

pytestmark = pytest.mark.integration
SLUG = "teste-integracao-quimera"


def _pacote(slug=SLUG):
    return {
        "versao": 1,
        "aviso": "Pacote sintético de teste.",
        "politicos": [
            {
                "slug": slug,
                "nome_completo": "Quimera Integração Teste",
                "nome_urna": "Quimera Integração",
                "cargo": "Deputada Federal",
                "uf": "GO",
                "partido": "CIDADANIA",
                "origem_dados": "demonstracao",
                "fonte_nome": "Teste",
                "mandatos": [
                    {
                        "cargo": "Deputada Federal",
                        "esfera": "federal",
                        "uf": "GO",
                        "inicio": "2023-02-01",
                        "origem_dados": "demonstracao",
                    }
                ],
                "projetos": [
                    {
                        "chave": "pl-t",
                        "casa": "camara",
                        "numero": 9099,
                        "ano": 2026,
                        "ementa": "Projeto sintético.",
                        "data_apresentacao": "2026-01-10",
                        "origem_dados": "demonstracao",
                    }
                ],
                "votacoes": [
                    {
                        "identificador_externo": "teste-vot-1",
                        "casa": "camara",
                        "projeto": "pl-t",
                        "data_votacao": "2026-02-01",
                        "voto": None,
                        "origem_dados": "demonstracao",
                    }
                ],
                "despesas": [
                    {
                        "categoria": "gabinete",
                        "descricao": "Item com valor",
                        "valor": "100.50",
                        "periodo_inicio": "2026-01-01",
                        "periodo_fim": "2026-01-31",
                        "origem_dados": "demonstracao",
                    },
                    {
                        "categoria": "consultoria",
                        "descricao": "Item sem valor",
                        "valor": None,
                        "periodo_inicio": "2026-02-01",
                        "periodo_fim": "2026-02-28",
                        "origem_dados": "demonstracao",
                    },
                ],
                "noticias": [
                    {
                        "titulo_original": "Quimera Integração Teste discute pauta (sintético)",
                        "url_original": "https://sintetica.example/integracao/quimera",
                        "publicado_em": "2026-03-01T12:00:00+00:00",
                        "resumo": "Apenas teste.",
                    }
                ],
            }
        ],
    }


@pytest.fixture()
def app():
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        yield app
        p = db.session.scalar(db.select(Politico).where(Politico.slug == SLUG))
        if p:
            db.session.execute(text("DELETE FROM noticia_politicos WHERE politico_id=:id"), {"id": p.id})
            db.session.execute(text("DELETE FROM noticias WHERE url_canonica LIKE :u"), {"u": "%sintetica.example/integracao/quimera%"})
            db.session.execute(text("DELETE FROM votacoes WHERE politico_id=:id"), {"id": p.id})
            db.session.execute(text("DELETE FROM projetos WHERE politico_id=:id"), {"id": p.id})
            db.session.execute(text("DELETE FROM mandatos WHERE politico_id=:id"), {"id": p.id})
            db.session.execute(text("DELETE FROM despesas WHERE politico_id=:id"), {"id": p.id})
            db.session.execute(text("DELETE FROM politicos WHERE id=:id"), {"id": p.id})
            db.session.commit()


def test_importacao_idempotente_filtros_e_dados_ausentes(app):
    c = app.test_client()
    with app.app_context():
        r1 = importar_pacote(_pacote())
        r2 = importar_pacote(_pacote())
        assert r1["politicos_novos"] == 1
        assert r2["politicos_novos"] == 0
        assert r2["despesas_novas"] == 0
        p = db.session.scalar(db.select(Politico).where(Politico.slug == SLUG))
        pid = p.id

    lista = c.get("/api/politicos?q=Quimera Integração&uf=GO").get_json()
    assert lista["total"] >= 1
    assert any(i["id"] == pid for i in lista["items"])
    assert all(i.get("demonstracao") is True for i in lista["items"] if i["id"] == pid)

    injecao = c.get("/api/politicos?q=%27+OR+1%3D1&per_page=50").get_json()
    assert injecao["total"] == 0

    perfil = c.get(f"/api/politicos/{pid}").get_json()
    assert perfil["id"] == pid
    assert len(perfil["mandatos"]) == 1
    assert len(perfil["projetos"]) == 1
    assert perfil["votacoes"][0]["voto"] is None
    financeiro = perfil["resumo_financeiro"]
    assert financeiro["registros_sem_valor"] == 1
    assert financeiro["completo"] is False
    assert financeiro["soma_valores_informados"] == "100.50"

    noticias = c.get(f"/api/politicos/{pid}/noticias").get_json()
    assert noticias["total"] >= 1
    assert all(any(pol["id"] == pid for pol in n["politicos"]) for n in noticias["items"])

    despesas = c.get(f"/api/transparencia/despesas?uf=GO&categoria=consultoria").get_json()
    valores = [i["valor"] for i in despesas["items"] if i["politico"] and i["politico"]["id"] == pid]
    assert None in valores
    assert "0.00" not in valores

    assert c.get("/api/politicos/999999999").status_code == 404
    assert c.get("/api/politicos?uf=XX").status_code == 400
    assert c.get("/api/politicos?per_page=999").status_code == 400
    pag = c.get("/api/politicos?per_page=1&page=1").get_json()
    assert pag["per_page"] == 1 and len(pag["items"]) <= 1
