"""Importação dos resultados de candidaturas eleitas publicados pelo TSE."""
import csv
import hashlib
import io
import re
import zipfile
from datetime import datetime, timezone

import requests
from sqlalchemy import select

from app.extensions import db
from app.models.cargo_eletivo import CargoEletivo
from app.models.dominios_eleitorais_transparencia import Candidatura
from app.models.politico import Politico

FONTE_NOME = "Tribunal Superior Eleitoral (TSE)"
PORTAL = "https://dadosabertos.tse.jus.br/dataset/candidatos-{ano}"
URLS_CANDIDATOS = {
    2022: "https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_2022.zip",
    2024: "https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_2024.zip",
}
CARGOS = {
    "PRESIDENTE": ("Presidente", "federal"),
    "GOVERNADOR": ("Governador", "estadual"),
    "SENADOR": ("Senador", "federal"),
    "DEPUTADO FEDERAL": ("Deputado Federal", "federal"),
    "DEPUTADO ESTADUAL": ("Deputado Estadual", "estadual"),
    "DEPUTADO DISTRITAL": ("Deputado Distrital", "estadual"),
    "PREFEITO": ("Prefeito", "municipal"),
    "VEREADOR": ("Vereador", "municipal"),
}


def _texto(row, campo):
    return (row.get(campo) or "").strip()


def _normalizar_linha(row):
    return {str(k or "").replace("\ufeff", "").strip().upper(): (v or "").strip() for k, v in row.items()}


def _e_eleito(row):
    return _texto(row, "DS_SIT_TOT_TURNO").upper().startswith("ELEITO")


def _cargo(row):
    return CARGOS.get(_texto(row, "DS_CARGO").upper())


def _slug_candidato(row, ano):
    cpf = re.sub(r"\D", "", _texto(row, "NR_CPF_CANDIDATO"))
    if cpf:
        return "tse-p-" + hashlib.sha256(cpf.encode("ascii")).hexdigest()[:32]
    return f"tse-{ano}-{_texto(row, 'SQ_CANDIDATO')}"


def _ler_csvs(conteudo, ano):
    with zipfile.ZipFile(io.BytesIO(conteudo)) as arquivo:
        candidatos = [
            nome for nome in arquivo.namelist()
            if nome.lower().endswith(".csv")
            and "consulta_cand_" in nome.lower()
            and "complementar" not in nome.lower()
        ]
        if not candidatos:
            raise ValueError(f"O arquivo do TSE para {ano} não contém CSV de candidaturas.")
        for nome in candidatos:
            with arquivo.open(nome) as binario:
                texto = io.TextIOWrapper(binario, encoding="latin1", newline="")
                leitor = csv.DictReader(texto, delimiter=";")
                for linha in leitor:
                    yield _normalizar_linha(linha)


def _politico(row, ano, cargo, uf, fonte_url, contexto):
    nome = _texto(row, "NM_CANDIDATO")
    nome_urna = _texto(row, "NM_URNA_CANDIDATO") or nome
    if not nome:
        return None
    slug = _slug_candidato(row, ano)
    politico = contexto["politicos_por_slug"].get(slug)

    # Reutiliza cadastros da Câmara/Senado apenas quando nome e UF coincidirem
    # exatamente, o registro oficial for único e não for demonstração; evita
    # associação por homônimo ou a promoção acidental de registros fictícios.
    if politico is None:
        correspondencias = [
            pessoa for pessoa in contexto["politicos_por_nome"].get(nome, [])
            if pessoa.origem_dados == "oficial" and (not uf or pessoa.uf == uf)
        ][:2]
        if len(correspondencias) == 1:
            politico = correspondencias[0]

    agora = datetime.now(timezone.utc)
    if politico is None:
        municipio = _texto(row, "NM_UE")[:120] if cargo in ("Prefeito", "Vereador") else None
        politico = Politico(
            slug=slug,
            nome_completo=nome[:200],
            nome_urna=nome_urna[:200],
            apelidos=[],
            cargo=cargo,
            uf=uf,
            municipio=municipio or None,
            partido=_texto(row, "SG_PARTIDO")[:20] or None,
            origem_dados="oficial",
            fonte_nome=FONTE_NOME,
            fonte_url=fonte_url,
            coletado_em=agora,
            atualizado_em=agora,
        )
        db.session.add(politico)
        db.session.flush()
        contexto["politicos_por_slug"][slug] = politico
        contexto["politicos_por_nome"].setdefault(nome, []).append(politico)
    else:
        politico.nome_urna = nome_urna[:200]
        if not politico.cargo:
            politico.cargo = cargo
        if not politico.uf:
            politico.uf = uf
        politico.origem_dados = "oficial"
        politico.fonte_nome = FONTE_NOME
        politico.fonte_url = fonte_url
        politico.atualizado_em = agora
    contexto["politicos_por_slug"].setdefault(slug, politico)
    return politico


def _upsert_eleicao(row, ano, contexto):
    detalhe_cargo = _cargo(row)
    codigo_candidato = _texto(row, "SQ_CANDIDATO")
    situacao = _texto(row, "DS_SIT_TOT_TURNO")
    if not detalhe_cargo or not codigo_candidato or not situacao or not _e_eleito(row):
        return False

    cargo, esfera = detalhe_cargo
    uf = _texto(row, "SG_UF").upper() or None
    if uf in ("BR", "ZZ"):
        uf = None
    municipio = _texto(row, "NM_UE") or None
    if cargo in ("Presidente", "Governador", "Senador", "Deputado Federal", "Deputado Estadual", "Deputado Distrital"):
        municipio = None
    fonte_url = PORTAL.format(ano=ano)
    politico = _politico(row, ano, cargo, uf, fonte_url, contexto)
    if politico is None:
        return False

    chave_candidatura = (politico.id, ano, cargo, uf, municipio)
    candidatura = contexto["candidaturas"].get(chave_candidatura)
    if candidatura is None:
        candidatura = Candidatura(
            politico_id=politico.id, ano=ano, cargo=cargo, uf=uf, municipio=municipio,
        )
        db.session.add(candidatura)
        contexto["candidaturas"][chave_candidatura] = candidatura
    candidatura.nome_urna = _texto(row, "NM_URNA_CANDIDATO")[:200] or None
    candidatura.sigla_partido = _texto(row, "SG_PARTIDO")[:32] or None
    candidatura.numero_candidatura = _texto(row, "NR_CANDIDATO")[:16] or None
    candidatura.resultado = situacao[:32]
    candidatura.votos = None  # O arquivo de candidaturas não é a fonte de votação nominal.
    candidatura.origem_dados = "oficial"
    candidatura.fonte_nome = FONTE_NOME
    candidatura.fonte_url = fonte_url

    origem = f"tse_{ano}"
    chave_cargo = (origem, codigo_candidato)
    cargo_eletivo = contexto["cargos"].get(chave_cargo)
    dados = {
        "politico_id": politico.id,
        "cargo": cargo,
        "esfera": esfera,
        "uf": uf,
        "municipio": municipio,
        "partido": _texto(row, "SG_PARTIDO")[:32] or None,
        "ano_eleicao": ano,
        "situacao": situacao[:64],
        "identificador_externo": codigo_candidato,
        "origem": origem,
        "fonte_nome": FONTE_NOME,
        "fonte_url": fonte_url,
        "dados_origem": {
            "codigo_candidato": codigo_candidato,
            "situacao_totalizacao": situacao,
            "nome_urna": _texto(row, "NM_URNA_CANDIDATO"),
            "cargo_tse": _texto(row, "DS_CARGO"),
        },
    }
    if cargo_eletivo is None:
        cargo_eletivo = CargoEletivo(**dados)
        db.session.add(cargo_eletivo)
        contexto["cargos"][chave_cargo] = cargo_eletivo
    else:
        for campo, valor in dados.items():
            setattr(cargo_eletivo, campo, valor)
        cargo_eletivo.atualizado_em = datetime.now(timezone.utc)
    return True


def sincronizar_tse(anos=(2022, 2024), session=None, baixar=None):
    """Importa candidatos eleitos de anos suportados a partir dos ZIPs oficiais."""
    session = session or requests.Session()
    baixar = baixar or session.get
    resumo = {"lidos": 0, "eleitos": 0, "anos": []}
    try:
        pessoas = db.session.scalars(select(Politico)).all()
        candidaturas = db.session.scalars(select(Candidatura)).all()
        cargos = db.session.scalars(select(CargoEletivo)).all()
        contexto = {
            "politicos_por_slug": {p.slug: p for p in pessoas if p.slug},
            "politicos_por_nome": {},
            "candidaturas": {
                (c.politico_id, c.ano, c.cargo, c.uf, c.municipio): c for c in candidaturas
            },
            "cargos": {
                (c.origem, c.identificador_externo): c for c in cargos
                if c.identificador_externo
            },
        }
        for pessoa in pessoas:
            contexto["politicos_por_nome"].setdefault(pessoa.nome_completo, []).append(pessoa)
        for ano in anos:
            ano = int(ano)
            if ano not in URLS_CANDIDATOS:
                raise ValueError(f"Ano {ano} não suportado. Anos disponíveis: 2022 e 2024.")
            resposta = baixar(URLS_CANDIDATOS[ano], timeout=120, headers={"User-Agent": "VotoTransparente/1.0 (dados públicos)"})
            resposta.raise_for_status()
            lidos = eleitos = 0
            for row in _ler_csvs(resposta.content, ano):
                lidos += 1
                if _upsert_eleicao(row, ano, contexto):
                    eleitos += 1
            resumo["lidos"] += lidos
            resumo["eleitos"] += eleitos
            resumo["anos"].append({"ano": ano, "lidos": lidos, "eleitos": eleitos})
            db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return resumo
