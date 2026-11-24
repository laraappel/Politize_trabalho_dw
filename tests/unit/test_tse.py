import io
import zipfile

from app.services.tse import _cargo, _e_eleito, _ler_csvs, _normalizar_linha, _slug_candidato


def test_normaliza_cabecalho_e_preserva_situacao_oficial():
    row = _normalizar_linha({" DS_CARGO": "PREFEITO ", "DS_SIT_TOT_TURNO": "ELEITO"})

    assert _cargo(row) == ("Prefeito", "municipal")
    assert _e_eleito(row) is True
    assert _e_eleito(_normalizar_linha({"DS_SIT_TOT_TURNO": "NÃO ELEITO"})) is False


def test_mapeia_cargos_por_esfera():
    esperados = {
        "PRESIDENTE": ("Presidente", "federal"),
        "GOVERNADOR": ("Governador", "estadual"),
        "SENADOR": ("Senador", "federal"),
        "DEPUTADO FEDERAL": ("Deputado Federal", "federal"),
        "DEPUTADO ESTADUAL": ("Deputado Estadual", "estadual"),
        "PREFEITO": ("Prefeito", "municipal"),
        "VEREADOR": ("Vereador", "municipal"),
    }
    for cargo_tse, esperado in esperados.items():
        assert _cargo({"DS_CARGO": cargo_tse}) == esperado


def test_identidade_tse_e_repetivel_sem_expor_cpf():
    registro = {"NR_CPF_CANDIDATO": "123.456.789-00"}
    slug = _slug_candidato(registro, 2024)

    assert slug == _slug_candidato(registro, 2022)
    assert "12345678900" not in slug


def test_leitura_do_zip_csv_em_latin1():
    conteudo = io.BytesIO()
    with zipfile.ZipFile(conteudo, "w") as arquivo:
        arquivo.writestr(
            "consulta_cand_2024_SP.csv",
            "DS_CARGO;NM_CANDIDATO;DS_SIT_TOT_TURNO\nPREFEITO;João Silva;ELEITO\n".encode("latin1"),
        )

    linhas = list(_ler_csvs(conteudo.getvalue(), 2024))

    assert linhas == [{
        "DS_CARGO": "PREFEITO",
        "NM_CANDIDATO": "João Silva",
        "DS_SIT_TOT_TURNO": "ELEITO",
    }]
