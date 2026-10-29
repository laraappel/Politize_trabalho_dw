"""Fluxo completo contra o PostgreSQL (coleta -> API). Dados sintéticos; limpa o que cria.

Requer DATABASE_URL apontando para um banco já migrado (`flask migrate`).
"""
import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import text

if not os.getenv("DATABASE_URL"):
    pytest.skip("DATABASE_URL não definido", allow_module_level=True)

from app import create_app
from app.extensions import db
from app.models.noticia import Noticia, PoliticoRef, Veiculo
from app.services.noticias.coleta import coletar_fonte, sincronizar_veiculos
from app.services.noticias.fontes.base import ErroColeta, FonteNoticias, ItemBruto

pytestmark = pytest.mark.integration
TOKEN = "token-de-teste"


class FonteFalsa(FonteNoticias):
    """Fonte sintética para testar o pipeline sem rede."""

    slug, nome, dominio = "fonte-sintetica-teste", "Fonte Sintética (teste)", "sintetica.example"
    tipo, autorizada, permite_resumo = "imprensa", True, True
    base_autorizacao = "Somente testes."

    def __init__(self, itens=None, erro=None):
        self.itens, self.erro = itens or [], erro

    def coletar(self):
        if self.erro:
            raise ErroColeta(self.erro)
        return self.itens


def item(n, titulo, dia=5, **kw):
    return ItemBruto(
        titulo=titulo,
        url=f"https://sintetica.example/politica/{n}?utm_source=x",
        guid=f"g{n}",
        publicado_em=datetime(2026, 3, dia, 12, tzinfo=timezone.utc),
        resumo=kw.pop("resumo", "Resumo curto sintético."),
        assunto_padrao=("politica", "Política"),
        **kw,
    )


@pytest.fixture()
def app(monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", TOKEN)
    monkeypatch.setenv("NOTICIAS_INTERVALO_MIN_SEGUNDOS", "0")
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        ids = []
        for nome, urna, cargo in [
            ("Zeferino Quimera Sintético", "Zeferino Quimera", "Deputado Federal"),
            ("Marlene Fantasia Teste", None, "Senadora"),
        ]:
            p = PoliticoRef(nome_completo=nome, nome_urna=urna, cargo=cargo, apelidos=[])
            db.session.add(p)
            db.session.flush()
            ids.append(p.id)
        db.session.commit()
        app.config["_IDS"] = ids
        yield app
        db.session.rollback()
        v = db.session.scalar(db.select(Veiculo).where(Veiculo.slug == FonteFalsa.slug))
        if v:
            db.session.execute(text("DELETE FROM noticias WHERE veiculo_id=:v"), {"v": v.id})
            db.session.execute(text("DELETE FROM coletas_noticias WHERE veiculo_id=:v"), {"v": v.id})
            db.session.execute(text("DELETE FROM veiculos WHERE id=:v"), {"v": v.id})
        db.session.execute(text("DELETE FROM politicos WHERE id = ANY(:ids)"), {"ids": ids})
        db.session.commit()


def coletar(app, itens=None, erro=None):
    f = FonteFalsa(itens, erro)
    return coletar_fonte(f.slug, forcar=True, fontes={f.slug: f})


def test_pipeline_api_e_neutralidade(app):
    zef, mar = app.config["_IDS"]
    c = app.test_client()
    itens = [
        item(1, "Deputado Zeferino Quimera apresenta projeto", dia=5),
        item(2, "Zeferino Quimera é visto em evento", dia=6),  # só nome: pendente
        item(3, "Economia cresce", dia=7),  # sem político: descartada
        item(4, "Senadora Marlene Fantasia Teste é investigada pela PF", dia=8),
        item(1, "Deputado Zeferino Quimera apresenta projeto", dia=5),  # duplicata exata
    ]
    r = coletar(app, itens)
    assert r.status == "ok" and r.itens_novos == 3 and r.itens_descartados == 1  # a duplicata vira "inalterado"

    # Idempotência: nova coleta não cria nada.
    r2 = coletar(app, itens)
    assert r2.itens_novos == 0

    pub = c.get("/api/noticias?per_page=50").get_json()
    titulos = {i["titulo_original"] for i in pub["items"] if i["veiculo"]["slug"] == FonteFalsa.slug}
    assert "Zeferino Quimera é visto em evento" not in titulos  # pendente_revisao não é público
    assert "Economia cresce" not in titulos
    assert len(titulos) == 2

    # URL original preservada (com parâmetros), canônica só para dedup.
    n1 = next(i for i in pub["items"] if i["titulo_original"].startswith("Deputado Zeferino"))
    assert n1["url_original"].endswith("?utm_source=x")
    assert n1["politicos"][0]["grau_confirmacao"] == "alta"
    assert n1["natureza"]["codigo"] == "nao_classificado"

    # Investigação é rotulada e traz aviso de não-culpa.
    n4 = next(i for i in pub["items"] if "investigada" in i["titulo_original"])
    assert n4["natureza"]["codigo"] == "investigacao" and "culpa" in n4["natureza"]["aviso"]

    # Filtros, ordenação e paginação.
    por_pol = c.get(f"/api/noticias?politico={zef}").get_json()
    assert por_pol["total"] == 1
    assert c.get("/api/noticias?natureza=investigacao&veiculo=fonte-sintetica-teste").get_json()["total"] == 1
    assert c.get("/api/noticias?de=2026-03-08&ate=2026-03-08&veiculo=fonte-sintetica-teste").get_json()["total"] == 1
    antigas = c.get("/api/noticias?ordem=antigas&veiculo=fonte-sintetica-teste").get_json()["items"]
    assert [i["publicado_em"] for i in antigas] == sorted(i["publicado_em"] for i in antigas)
    p1 = c.get("/api/noticias?per_page=1&page=1&veiculo=fonte-sintetica-teste").get_json()
    assert p1["total"] == 2 and p1["pages"] == 2 and len(p1["items"]) == 1
    filtros = c.get("/api/noticias/filtros").get_json()
    assert any(p["id"] == zef for p in filtros["politicos"])

    # Notícias do político (perfil).
    assert c.get(f"/api/politicos/{zef}/noticias").get_json()["total"] == 1
    assert c.get("/api/politicos/999999999/noticias").status_code == 404

    # Validação de parâmetros.
    for q in ("ordem=x", "de=ontem", "per_page=999", "natureza=boato", "de=2026-03-10&ate=2026-03-01"):
        resp = c.get(f"/api/noticias?{q}")
        assert resp.status_code == 400 and resp.get_json()["error"] == "parametro_invalido"


def test_revisao_editorial_e_atualizacoes(app):
    zef, _ = app.config["_IDS"]
    c = app.test_client()
    coletar(app, [item(10, "Zeferino Quimera participa de debate")])
    with app.app_context():
        nid = db.session.scalar(db.select(Noticia.id).where(Noticia.guid_origem == "g10"))
    H = {"X-Admin-Token": TOKEN}

    # Sem token ou com token errado: bloqueado.
    assert c.get("/api/noticias/revisao").status_code == 401
    assert c.get("/api/noticias/revisao", headers={"X-Admin-Token": "errado"}).status_code == 401
    assert c.get(f"/api/noticias/{nid}").status_code == 404  # ainda não pública

    pend = c.get("/api/noticias/revisao", headers=H).get_json()["items"]
    assert any(p["noticia_id"] == nid and p["metodo"] == "nome_completo" for p in pend)

    # Revisão exige revisor identificado.
    url = f"/api/noticias/{nid}/politicos/{zef}/revisao"
    assert c.post(url, json={"decisao": "confirmar"}, headers=H).status_code == 400
    assert c.post(url, json={"decisao": "confirmar", "revisado_por": "ana"}, headers=H).status_code == 200
    det = c.get(f"/api/noticias/{nid}").get_json()
    assert det["politicos"][0]["origem"] == "manual" and det["politicos"][0]["grau_confirmacao"] == "manual"
    assert det["politicos"][0]["evidencias"]  # evidência automática preservada

    # Nova coleta não sobrescreve decisão manual.
    coletar(app, [item(10, "Zeferino Quimera participa de debate")])
    assert c.get(f"/api/noticias/{nid}").get_json()["politicos"][0]["origem"] == "manual"

    # Reclassificação e desdobramento.
    assert c.patch(f"/api/noticias/{nid}/natureza", json={"natureza": "fato_documentado"}, headers=H).status_code == 200
    r = c.post(f"/api/noticias/{nid}/atualizacoes", headers=H,
               json={"tipo": "desdobramento", "descricao": "Caso arquivado.", "url_referencia": "https://orgao.example/x", "criado_por": "ana"})
    assert r.status_code == 201
    assert c.post(f"/api/noticias/{nid}/atualizacoes", headers=H, json={"tipo": "x", "descricao": "y"}).status_code == 400
    assert c.post(f"/api/noticias/{nid}/atualizacoes", headers=H, json={"tipo": "correcao", "descricao": "y", "url_referencia": "javascript:alert(1)"}).status_code == 400
    det = c.get(f"/api/noticias/{nid}").get_json()
    assert det["natureza"]["codigo"] == "fato_documentado" and det["natureza"]["origem"] == "editorial"
    assert det["atualizacoes"][0]["tipo"] == "desdobramento"

    # Rejeição remove da API pública.
    c.post(url, json={"decisao": "rejeitar", "revisado_por": "ana"}, headers=H)
    assert c.get(f"/api/noticias/{nid}").status_code == 404
    coletar(app, [item(10, "Zeferino Quimera participa de debate")])  # recoleta não reabre
    assert c.get(f"/api/noticias/{nid}").status_code == 404


def test_titulo_alterado_gera_atualizacao_e_erro_de_fonte_e_registrado(app):
    c = app.test_client()
    coletar(app, [item(20, "Deputado Zeferino Quimera propõe lei")])
    coletar(app, [item(20, "Deputado Zeferino Quimera propõe nova lei")])
    with app.app_context():
        nid = db.session.scalar(db.select(Noticia.id).where(Noticia.guid_origem == "g20"))
    det = c.get(f"/api/noticias/{nid}").get_json()
    assert det["titulo_original"].endswith("nova lei")
    assert det["atualizacoes"][0]["tipo"] == "alteracao_titulo" and "propõe lei" in det["atualizacoes"][0]["descricao"]

    r = coletar(app, erro="falha simulada")
    assert r.status == "erro" and "falha simulada" in r.mensagem


def test_admin_desabilitado_sem_token_configurado(app, monkeypatch):
    monkeypatch.delenv("ADMIN_TOKEN")
    assert app.test_client().get("/api/noticias/revisao").status_code == 403


def test_veiculos_expoe_base_de_autorizacao(app):
    with app.app_context():
        sincronizar_veiculos()
    items = app.test_client().get("/api/veiculos").get_json()["items"]
    por_slug = {v["slug"]: v for v in items}
    assert por_slug["agencia-brasil"]["coleta_autorizada"] is True
    assert por_slug["g1"]["coleta_autorizada"] is False and por_slug["folha"]["base_autorizacao"]
