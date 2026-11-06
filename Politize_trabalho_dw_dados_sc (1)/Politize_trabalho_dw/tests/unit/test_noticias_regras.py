"""Testes das regras puras do módulo de notícias. Dados 100% sintéticos."""
from datetime import datetime, timezone

import pytest

from app.services.noticias.associacao import AssociadorPoliticos, PoliticoCadastro
from app.services.noticias.classificacao import classificar_natureza
from app.services.noticias.fontes.agencia_brasil import limpar_resumo, parse_rss
from app.services.noticias.fontes.base import ErroColeta, FonteNaoAutorizada
from app.services.noticias.fontes.nao_autorizadas import CnnBrasil, FolhaDeSPaulo, G1
from app.services.noticias.normalizacao import canonicalizar_url, chave_dedup, normalizar_texto

ANA = PoliticoCadastro(1, "Ana Beatriz Exemplo Souza", "Ana Exemplo", ("Aninha Exemplo",), "Deputada Federal", "XX", 111)
JOAO_A = PoliticoCadastro(2, "João Teste Silva", None, (), "Senador")
JOAO_B = PoliticoCadastro(3, "João Teste Silva", None, (), "Prefeito")
CURTO = PoliticoCadastro(4, "Carlos Lima", None, (), "Vereador")
LONGO = PoliticoCadastro(5, "Carlos Lima Junior", None, (), "Vereador")


def assoc(politicos, titulo, resumo=None, links=""):
    return {a.politico_id: a for a in AssociadorPoliticos(politicos).associar(titulo, resumo, links)}


def test_nome_completo_com_cargo_confirma_com_evidencia():
    r = assoc([ANA], "Deputada Ana Exemplo apresenta projeto")
    assert r[1].status == "confirmada" and r[1].grau == "alta"
    assert r[1].metodo == "nome_completo_e_cargo"
    assert r[1].evidencias[0]["campo"] == "titulo" and "Ana Exemplo" in r[1].evidencias[0]["trecho"]


def test_nome_sem_contexto_nao_confirma_automaticamente():
    r = assoc([ANA], "Ana Exemplo participa de evento")
    assert r[1].status == "pendente_revisao" and r[1].grau == "media"


def test_homonimos_nunca_confirmam_nem_com_cargo():
    r = assoc([JOAO_A, JOAO_B], "Senador João Teste Silva critica proposta")
    assert {a.status for a in r.values()} == {"pendente_revisao"}
    assert all(a.metodo == "homonimia" and a.grau == "baixa" for a in r.values())


def test_apelido_sozinho_e_ignorado_e_com_cargo_vai_para_revisao():
    assert assoc([ANA], "Aninha Exemplo foi ao cinema") == {}
    r = assoc([ANA], "Deputada Aninha Exemplo vota hoje")
    assert r[1].status == "pendente_revisao" and r[1].metodo == "apelido_e_cargo"


def test_nome_curto_dentro_de_nome_longo_nao_associa_o_curto():
    r = assoc([CURTO, LONGO], "Vereador Carlos Lima Junior discursa")
    assert 5 in r and 4 not in r


def test_sem_coincidencia_nada_e_associado():
    assert assoc([ANA], "Economia cresce no trimestre") == {}


def test_identificador_oficial_confirma():
    r = assoc([ANA], "Projeto avança", links='<a href="https://www.camara.leg.br/deputados/111">perfil</a>')
    assert r[1].status == "confirmada" and r[1].metodo == "identificador_oficial"


def test_identificador_desconhecido_nao_associa():
    assert assoc([ANA], "Projeto avança", links="camara.leg.br/deputados/999") == {}


def test_acentos_e_caixa_nao_atrapalham():
    r = assoc([JOAO_A], "SENADOR JOAO TESTE SILVA fala")
    assert r[2].status == "confirmada"


@pytest.mark.parametrize(
    "titulo,esperado",
    [
        ("PF abre inquérito para investigar deputado", "investigacao"),
        ("Opinião: o que esperar da reforma", "opiniao"),
        ("Opinião sobre inquérito da PF", "opiniao"),  # opinião prevalece
        ("Deputado é acusado de omitir bens", "alegacao"),
        ("Câmara aprova projeto", "nao_classificado"),
    ],
)
def test_classificacao_conservadora(titulo, esperado):
    assert classificar_natureza(titulo) == esperado


def test_nunca_classifica_fato_documentado_automaticamente():
    for t in ("Presidente sanciona lei", "Senado aprova PEC", "Decreto publicado no Diário Oficial"):
        assert classificar_natureza(t) != "fato_documentado"


def test_url_canonica_remove_rastreamento_e_unifica():
    a = canonicalizar_url("http://Exemplo.com.br/politica/noticia/x/?utm_source=a&id=1#topo")
    b = canonicalizar_url("https://exemplo.com.br/politica/noticia/x?id=1&fbclid=zzz")
    assert a == b == "https://exemplo.com.br/politica/noticia/x?id=1"


def test_chave_dedup_ignora_caixa_acento_e_hora():
    d1 = datetime(2026, 1, 5, 9, tzinfo=timezone.utc)
    d2 = datetime(2026, 1, 5, 21, tzinfo=timezone.utc)
    assert chave_dedup("v", "Título  Ótimo!", d1) == chave_dedup("v", "titulo otimo", d2)
    assert normalizar_texto("Ação") == "acao"


# --- RSS: fixture SINTÉTICA (formato RSS 2.0), não são notícias reais ---
RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/"><channel>
<item><title>Deputada Ana Exemplo &amp; projeto</title>
<link>https://agenciabrasil.ebc.com.br/politica/noticia/2026-01/teste-1?utm_source=rss</link>
<guid isPermaLink="false">sintetico-1</guid><pubDate>Mon, 05 Jan 2026 10:00:00 -0300</pubDate>
<category>Política</category>
<description>&lt;p&gt;Texto &lt;b&gt;curto&lt;/b&gt; de teste.&lt;/p&gt;&lt;img src="https://agenciabrasil.ebc.com.br/ebc.png?id=1&amp;o=rss"/&gt;</description></item>
<item><title>Link de outro domínio</title><link>https://outro.example/x</link></item>
<item><title>Sem link</title></item>
<item><title>Matéria de agência parceira</title><link>https://agenciabrasil.ebc.com.br/internacional/noticia/2026-01/teste-2</link>
<description>Texto cedido pela Reuters para teste.</description></item>
</channel></rss>""".encode()


def test_parse_rss_extrai_metadados_e_filtra():
    itens = parse_rss(RSS, "politica", "agenciabrasil.ebc.com.br")
    assert [i.guid for i in itens] == ["sintetico-1", None]
    i = itens[0]
    assert i.titulo == "Deputada Ana Exemplo & projeto"
    assert i.resumo == "Texto curto de teste."  # sem HTML nem pixel de rastreamento
    assert i.publicado_em == datetime(2026, 1, 5, 13, tzinfo=timezone.utc)
    assert i.assunto_padrao == ("politica", "Política")
    assert itens[1].resumo is None  # agência parceira: sem resumo


def test_parse_rss_rejeita_xml_invalido_e_entidades_externas():
    with pytest.raises(ErroColeta):
        parse_rss(b"<rss><channel>", "politica", "x.com")
    xxe = b'<?xml version="1.0"?><!DOCTYPE r [<!ENTITY e SYSTEM "file:///etc/passwd">]><rss><channel><item><title>&e;</title><link>https://x.com/a</link></item></channel></rss>'
    with pytest.raises(ErroColeta):
        parse_rss(xxe, "politica", "x.com")


def test_resumo_truncado_em_palavra_inteira():
    r = limpar_resumo("palavra " * 100, 50)
    assert len(r) <= 51 and r.endswith("…") and "palavr…" not in r


@pytest.mark.parametrize("cls", [G1, CnnBrasil, FolhaDeSPaulo])
def test_fontes_sem_autorizacao_recusam_coleta(cls):
    f = cls()
    assert f.autorizada is False
    with pytest.raises(FonteNaoAutorizada):
        f.coletar()
