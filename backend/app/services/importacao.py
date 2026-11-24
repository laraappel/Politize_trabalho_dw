"""Importação idempotente de pacotes JSON (demonstração ou oficiais)."""
import json
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlsplit

from sqlalchemy import select

from app.dominio_constantes import ESFERAS, ORIGENS, UFS, VOTOS
from app.errors import ErroValidacao
from app.extensions import db
from app.models.dominio import Despesa, Mandato, Projeto, Votacao
from app.models.noticia import Noticia, NoticiaPolitico, Veiculo
from app.models.politico import Politico
from app.models.partido import Partido
from app.models.dominios_eleitorais_transparencia import (
    Candidatura,
    PatrimonioDeclarado,
    ProjetoCoautoria,
    PropostaCampanha,
    Remuneracao,
)
from app.services.noticias.normalizacao import canonicalizar_url, chave_dedup

VEICULO_DEMO = {
    "slug": "demonstracao",
    "nome": "Fonte de demonstração",
    "dominio": "demonstracao.vototransparente.local",
    "tipo": "imprensa",
    "coleta_autorizada": False,
    "permite_resumo": True,
    "base_autorizacao": "Registros fictícios do conjunto de demonstração. Não são matérias reais.",
    "url_termos": None,
}


def _origem(item, padrao="demonstracao"):
    codigo = item.get("origem_dados") or padrao
    if not isinstance(codigo, str):
        raise ErroValidacao("parametro_invalido", "origem_dados deve ser texto.")
    codigo = codigo.strip()
    if codigo not in ORIGENS:
        raise ErroValidacao("parametro_invalido", f"origem_dados inválida: {codigo}")
    if codigo == "oficial":
        nome = _texto(item.get("fonte_nome"), 200)
        url = _texto(item.get("fonte_url"))
        if not nome or not _url_http(url):
            raise ErroValidacao(
                "parametro_invalido",
                "Registros oficiais exigem fonte_nome e fonte_url HTTP(S).",
            )
    return codigo


def _uf(valor):
    if not valor:
        return None
    uf = str(valor).strip().upper()
    if uf not in UFS:
        raise ErroValidacao("parametro_invalido", f"UF inválida: {uf}")
    return uf


def _data(valor, nome):
    if valor in (None, ""):
        return None
    if isinstance(valor, date) and not isinstance(valor, datetime):
        return valor
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        raise ErroValidacao("parametro_invalido", f"'{nome}' deve estar no formato AAAA-MM-DD.")


def _datetime(valor):
    if valor in (None, ""):
        return None
    if isinstance(valor, datetime):
        return valor
    texto = str(valor)
    try:
        return datetime.fromisoformat(texto.replace("Z", "+00:00"))
    except ValueError:
        raise ErroValidacao("parametro_invalido", "Data/hora inválida.")


def _dinheiro(valor, nome):
    if valor in (None, ""):
        return None
    try:
        return Decimal(str(valor))
    except (InvalidOperation, ValueError):
        raise ErroValidacao("parametro_invalido", f"'{nome}' não é um valor financeiro válido.")


def _texto(valor, maximo=None):
    if valor in (None, ""):
        return None
    texto = str(valor).strip()
    if maximo:
        texto = texto[:maximo]
    return texto or None


def _url_http(valor):
    if not isinstance(valor, str) or not valor or len(valor) > 2048:
        return False
    try:
        partes = urlsplit(valor)
    except ValueError:
        return False
    return partes.scheme in ("http", "https") and bool(partes.netloc)


def validar_pacote(pacote: dict):
    if not isinstance(pacote, dict):
        raise ErroValidacao("parametro_invalido", "O pacote deve ser um objeto JSON.")
    if pacote.get("versao") != 1:
        raise ErroValidacao("parametro_invalido", "Apenas pacotes na versão 1 são aceitos.")
    if not isinstance(pacote.get("politicos"), list):
        raise ErroValidacao("parametro_invalido", "'politicos' deve ser uma lista.")


def _veiculo_demo() -> Veiculo:
    v = db.session.scalar(select(Veiculo).where(Veiculo.slug == VEICULO_DEMO["slug"]))
    if v is None:
        v = Veiculo(**VEICULO_DEMO)
        db.session.add(v)
        db.session.flush()
        return v
    for chave, valor in VEICULO_DEMO.items():
        setattr(v, chave, valor)
    return v


def _upsert_politico(item: dict) -> tuple[Politico, bool]:
    origem = _origem(item)
    slug = _texto(item.get("slug") or item.get("chave"), 80)
    if not slug:
        raise ErroValidacao("parametro_invalido", "Cada político precisa de um slug estável.")
    p = db.session.scalar(select(Politico).where(Politico.slug == slug))
    novo = p is None
    if novo:
        p = Politico(slug=slug, nome_completo=item.get("nome_completo") or slug)
        db.session.add(p)
    p.nome_completo = _texto(item.get("nome_completo"), 200) or p.nome_completo
    p.nome_urna = _texto(item.get("nome_urna"), 200)
    p.apelidos = list(item.get("apelidos") or [])
    p.cargo = _texto(item.get("cargo"), 80)
    p.uf = _uf(item.get("uf"))
    p.municipio = _texto(item.get("municipio"), 120)
    p.partido = _texto(item.get("partido"), 20)
    p.id_camara = item.get("id_camara")
    p.id_senado = item.get("id_senado")
    p.origem_dados = origem
    p.fonte_nome = _texto(item.get("fonte_nome"), 200)
    p.fonte_url = _texto(item.get("fonte_url"))
    db.session.flush()
    return p, novo


def _upsert_mandato(politico_id, item):
    origem = _origem(item)
    cargo = _texto(item.get("cargo"), 80)
    inicio = _data(item.get("inicio"), "inicio")
    if not cargo or not inicio:
        raise ErroValidacao("parametro_invalido", "Mandato exige cargo e inicio.")
    fim = _data(item.get("fim"), "fim")
    if fim and fim < inicio:
        raise ErroValidacao("parametro_invalido", "'fim' não pode ser anterior a 'inicio'.")
    esfera = (item.get("esfera") or "federal").strip()
    if esfera not in ESFERAS:
        raise ErroValidacao("parametro_invalido", f"Esfera inválida: {esfera}")
    existente = db.session.scalar(
        select(Mandato).where(
            Mandato.politico_id == politico_id,
            Mandato.cargo == cargo,
            Mandato.inicio == inicio,
        )
    )
    m = existente or Mandato(politico_id=politico_id, cargo=cargo, inicio=inicio)
    m.esfera = esfera
    m.uf = _uf(item.get("uf"))
    m.municipio = _texto(item.get("municipio"), 120)
    m.partido = _texto(item.get("partido"), 20)
    m.legislatura = _texto(item.get("legislatura"), 40)
    m.fim = fim
    m.origem_dados = origem
    m.fonte_nome = _texto(item.get("fonte_nome"), 200)
    m.fonte_url = _texto(item.get("fonte_url"))
    if existente is None:
        db.session.add(m)
    return existente is None


def _upsert_projeto(politico_id, item) -> tuple[Projeto, bool]:
    origem = _origem(item)
    casa = (_texto(item.get("casa"), 30) or "").lower()
    if not casa or item.get("numero") is None or item.get("ano") is None:
        raise ErroValidacao("parametro_invalido", "Projeto exige casa, numero e ano.")
    try:
        numero, ano = int(str(item["numero"])), int(str(item["ano"]))
    except (TypeError, ValueError):
        raise ErroValidacao("parametro_invalido", "'numero' e 'ano' do projeto devem ser inteiros.")
    if numero < 1 or ano < 1823:
        raise ErroValidacao("parametro_invalido", "'numero' e 'ano' do projeto estão fora do intervalo permitido.")
    existente = db.session.scalar(
        select(Projeto).where(Projeto.casa == casa, Projeto.numero == numero, Projeto.ano == ano)
    )
    pr = existente or Projeto(casa=casa, numero=numero, ano=ano)
    if existente is None:
        pr.politico_id = politico_id
    pr.ementa = _texto(item.get("ementa"))
    pr.situacao = _texto(item.get("situacao"), 40)
    pr.data_apresentacao = _data(item.get("data_apresentacao"), "data_apresentacao")
    pr.url_oficial = _texto(item.get("url_oficial"))
    pr.origem_dados = origem
    pr.fonte_nome = _texto(item.get("fonte_nome"), 200)
    pr.fonte_url = _texto(item.get("fonte_url"))
    if existente is None:
        db.session.add(pr)
        db.session.flush()
    return pr, existente is None


def _upsert_votacao(politico_id, item, projetos_por_chave: dict):
    origem = _origem(item)
    ident = _texto(item.get("identificador_externo"), 80)
    casa = _texto(item.get("casa"), 30)
    if not ident or not casa:
        raise ErroValidacao("parametro_invalido", "Votação exige identificador_externo e casa.")
    voto = item.get("voto")
    if voto in ("", None):
        voto = None
    elif voto not in VOTOS:
        raise ErroValidacao("parametro_invalido", f"Voto inválido: {voto}")
    chave_proj = item.get("projeto")
    projeto = projetos_por_chave.get(chave_proj) if chave_proj else None
    if chave_proj and projeto is None:
        raise ErroValidacao(
            "parametro_invalido",
            f"Votação referencia projeto inexistente no pacote: {chave_proj}.",
        )
    existente = db.session.scalar(
        select(Votacao).where(
            Votacao.politico_id == politico_id,
            Votacao.identificador_externo == ident,
        )
    )
    v = existente or Votacao(politico_id=politico_id, identificador_externo=ident)
    v.casa = casa
    v.data_votacao = _data(item.get("data_votacao"), "data_votacao")
    v.ementa = _texto(item.get("ementa"))
    v.voto = voto
    v.url_oficial = _texto(item.get("url_oficial"))
    v.origem_dados = origem
    v.fonte_nome = _texto(item.get("fonte_nome"), 200)
    v.fonte_url = _texto(item.get("fonte_url"))
    if projeto is not None:
        v.projeto_id = projeto.id
    if existente is None:
        db.session.add(v)
    return existente is None


def _upsert_despesa(politico_id, item):
    origem = _origem(item)
    categoria = _texto(item.get("categoria"), 80)
    descricao = _texto(item.get("descricao"))
    inicio = _data(item.get("periodo_inicio") or (item.get("periodo") or {}).get("inicio"), "periodo_inicio")
    fim = _data(item.get("periodo_fim") or (item.get("periodo") or {}).get("fim"), "periodo_fim")
    if not categoria or not descricao or not inicio or not fim:
        raise ErroValidacao("parametro_invalido", "Despesa exige categoria, descricao e período.")
    if fim < inicio:
        raise ErroValidacao("parametro_invalido", "'periodo_fim' não pode ser anterior a 'periodo_inicio'.")
    existente = db.session.scalar(
        select(Despesa).where(
            Despesa.politico_id == politico_id,
            Despesa.categoria == categoria,
            Despesa.periodo_inicio == inicio,
            Despesa.periodo_fim == fim,
            Despesa.descricao == descricao,
        )
    )
    d = existente or Despesa(
        politico_id=politico_id,
        categoria=categoria,
        descricao=descricao,
        periodo_inicio=inicio,
        periodo_fim=fim,
    )
    d.valor = _dinheiro(item.get("valor"), "valor")
    d.esfera = _texto(item.get("esfera"), 20)
    d.origem_dados = origem
    d.fonte_nome = _texto(item.get("fonte_nome"), 200)
    d.fonte_url = _texto(item.get("fonte_url"))
    if existente is None:
        db.session.add(d)
    return existente is None


def _upsert_noticia(politico: Politico, item, veiculo: Veiculo):
    url = _texto(item.get("url_original"))
    titulo = _texto(item.get("titulo_original"))
    if not _url_http(url) or not titulo:
        raise ErroValidacao("parametro_invalido", "Notícia de demonstração exige título e URL.")
    canonica = canonicalizar_url(url)
    publicado = _datetime(item.get("publicado_em"))
    chave = chave_dedup(veiculo.slug, titulo, publicado)
    n = db.session.scalar(select(Noticia).where(Noticia.url_canonica == canonica))
    novo = n is None
    if novo:
        n = Noticia(
            veiculo_id=veiculo.id,
            url_original=url,
            url_canonica=canonica,
            guid_origem=_texto(item.get("guid")),
            chave_dedup=chave,
            titulo_original=titulo,
        )
        db.session.add(n)
        db.session.flush()
    n.titulo_original = titulo
    n.resumo = _texto(item.get("resumo"), 400)
    n.publicado_em = publicado
    n.assunto_slug = _texto(item.get("assunto_slug"), 80)
    n.assunto_nome = _texto(item.get("assunto_nome"), 120)
    n.natureza = item.get("natureza") or "nao_classificado"
    n.natureza_origem = item.get("natureza_origem") or "editorial"
    assoc = db.session.get(NoticiaPolitico, (n.id, politico.id))
    if assoc is None:
        db.session.add(
            NoticiaPolitico(
                noticia_id=n.id,
                politico_id=politico.id,
                status="confirmada",
                grau_confirmacao="manual",
                metodo="importacao",
                origem="manual",
                evidencias=[{"campo": "importacao", "trecho": "Associação explícita do pacote de dados."}],
            )
        )
    return novo


def _upsert_candidatura(politico_id, item):
    origem = _origem(item)
    ano = int(item["ano"]) if item.get("ano") is not None else None
    cargo = _texto(item.get("cargo"), 64)
    if ano is None or ano < 1890 or not cargo:
        raise ErroValidacao("parametro_invalido", "Candidatura exige ano e cargo válidos.")
    uf = _uf(item.get("uf"))
    municipio = _texto(item.get("municipio"), 120)
    existente = db.session.scalar(select(Candidatura).where(
        Candidatura.politico_id == politico_id,
        Candidatura.ano == ano,
        Candidatura.cargo == cargo,
        Candidatura.uf == uf,
        Candidatura.municipio == municipio,
    ))
    c = existente or Candidatura(politico_id=politico_id, ano=ano, cargo=cargo, uf=uf, municipio=municipio)
    c.nome_urna = _texto(item.get("nome_urna"), 200)
    c.sigla_partido = _texto(item.get("partido_sigla"), 32)
    c.numero_candidatura = _texto(item.get("numero_candidatura"), 16)
    c.resultado = _texto(item.get("resultado"), 32)
    c.votos = item.get("votos")
    c.origem_dados = origem
    c.fonte_nome = _texto(item.get("fonte_nome"), 200)
    c.fonte_url = _texto(item.get("fonte_url"))
    if existente is None:
        db.session.add(c)
        db.session.flush()
    return c, existente is None


def _upsert_proposta(candidatura, item):
    origem = _origem(item)
    titulo = _texto(item.get("titulo"), 255)
    if not titulo:
        raise ErroValidacao("parametro_invalido", "Proposta exige titulo.")
    existente = db.session.scalar(select(PropostaCampanha).where(
        PropostaCampanha.candidatura_id == candidatura.id,
        PropostaCampanha.titulo == titulo,
    ))
    p = existente or PropostaCampanha(candidatura_id=candidatura.id, titulo=titulo)
    p.descricao = _texto(item.get("descricao"))
    p.tema = _texto(item.get("tema"), 64)
    p.origem_dados = origem
    p.fonte_nome = _texto(item.get("fonte_nome"), 200)
    p.fonte_url = _texto(item.get("fonte_url"))
    if existente is None:
        db.session.add(p)
    return existente is None


def _upsert_coautoria(projeto, politico_id, item):
    origem = _origem(item)
    papel = item.get("papel") or "coautor"
    if papel not in ("autor", "coautor", "relator"):
        raise ErroValidacao("parametro_invalido", "Papel de coautoria inválido.")
    existente = db.session.scalar(select(ProjetoCoautoria).where(
        ProjetoCoautoria.projeto_id == projeto.id,
        ProjetoCoautoria.politico_id == politico_id,
    ))
    c = existente or ProjetoCoautoria(projeto_id=projeto.id, politico_id=politico_id)
    c.papel = papel
    c.origem_dados = origem
    c.fonte_nome = _texto(item.get("fonte_nome"), 200)
    c.fonte_url = _texto(item.get("fonte_url"))
    if existente is None:
        db.session.add(c)
    return existente is None


def _upsert_remuneracao(politico_id, item):
    origem = _origem(item)
    cargo = _texto(item.get("cargo"), 120)
    inicio = _data(item.get("periodo_inicio") or (item.get("periodo") or {}).get("inicio"), "periodo_inicio")
    fim = _data(item.get("periodo_fim") or (item.get("periodo") or {}).get("fim"), "periodo_fim")
    if not inicio or not fim or fim < inicio:
        raise ErroValidacao("parametro_invalido", "Remuneração exige período válido.")
    existente = db.session.scalar(select(Remuneracao).where(
        Remuneracao.politico_id == politico_id,
        Remuneracao.cargo == cargo,
        Remuneracao.periodo_inicio == inicio,
        Remuneracao.periodo_fim == fim,
    ))
    r = existente or Remuneracao(politico_id=politico_id, cargo=cargo, periodo_inicio=inicio, periodo_fim=fim)
    r.valor_bruto = _dinheiro(item.get("valor_bruto"), "valor_bruto")
    r.beneficios = _dinheiro(item.get("beneficios"), "beneficios")
    r.descontos = _dinheiro(item.get("descontos"), "descontos")
    r.valor_liquido = _dinheiro(item.get("valor_liquido"), "valor_liquido")
    r.origem_dados = origem
    r.fonte_nome = _texto(item.get("fonte_nome"), 200)
    r.fonte_url = _texto(item.get("fonte_url"))
    if existente is None:
        db.session.add(r)
    return existente is None


def _upsert_patrimonio(politico_id, item):
    origem = _origem(item)
    try:
        ano = int(item["ano_referencia"])
    except (KeyError, TypeError, ValueError):
        raise ErroValidacao("parametro_invalido", "Patrimônio exige ano_referencia inteiro.")
    tipo = _texto(item.get("tipo"), 80)
    if ano < 1985 or not tipo:
        raise ErroValidacao("parametro_invalido", "Patrimônio exige ano_referencia e tipo válidos.")
    c = db.session.get(Candidatura, item["candidatura_id"]) if item.get("candidatura_id") else None
    if item.get("candidatura_id") and c is None:
        raise ErroValidacao("parametro_invalido", "candidatura_id inexistente.")
    existente = db.session.scalar(select(PatrimonioDeclarado).where(
        PatrimonioDeclarado.politico_id == politico_id,
        PatrimonioDeclarado.ano_referencia == ano,
        PatrimonioDeclarado.tipo == tipo,
        PatrimonioDeclarado.descricao == _texto(item.get("descricao")),
    ))
    p = existente or PatrimonioDeclarado(politico_id=politico_id, ano_referencia=ano, tipo=tipo)
    p.candidatura_id = c.id if c else None
    p.descricao = _texto(item.get("descricao"))
    p.valor = _dinheiro(item.get("valor"), "valor")
    p.localizacao = _texto(item.get("localizacao"), 255)
    p.origem_dados = origem
    p.fonte_nome = _texto(item.get("fonte_nome"), 200)
    p.fonte_url = _texto(item.get("fonte_url"))
    if existente is None:
        db.session.add(p)
    return existente is None


def importar_pacote(pacote: dict) -> dict:
    validar_pacote(pacote)
    resumo = {
        "aviso": pacote.get("aviso"),
        "politicos_novos": 0,
        "politicos_existentes": 0,
        "mandatos_novos": 0,
        "projetos_novos": 0,
        "votacoes_novas": 0,
        "despesas_novas": 0,
        "candidaturas_novas": 0,
        "propostas_novas": 0,
        "coautorias_novas": 0,
        "remuneracoes_novas": 0,
        "patrimonios_novos": 0,
        "noticias_novas": 0,
    }
    veiculo = _veiculo_demo()
    for item in pacote["politicos"]:
        politico, novo = _upsert_politico(item)
        resumo["politicos_novos" if novo else "politicos_existentes"] += 1
        for m in item.get("mandatos") or []:
            if _upsert_mandato(politico.id, m):
                resumo["mandatos_novos"] += 1
        projetos_por_chave = {}
        for pr in item.get("projetos") or []:
            obj, criado = _upsert_projeto(politico.id, pr)
            chave = pr.get("chave") or f"{obj.casa}-{obj.numero}-{obj.ano}"
            projetos_por_chave[chave] = obj
            if criado:
                resumo["projetos_novos"] += 1
        for v in item.get("votacoes") or []:
            if _upsert_votacao(politico.id, v, projetos_por_chave):
                resumo["votacoes_novas"] += 1
        for d in item.get("despesas") or []:
            if _upsert_despesa(politico.id, d):
                resumo["despesas_novas"] += 1
        for cand in item.get("candidaturas") or []:
            c, criado = _upsert_candidatura(politico.id, cand)
            if criado:
                resumo["candidaturas_novas"] += 1
            for proposta in cand.get("propostas") or []:
                if _upsert_proposta(c, proposta):
                    resumo["propostas_novas"] += 1
        for rem in item.get("remuneracoes") or []:
            if _upsert_remuneracao(politico.id, rem):
                resumo["remuneracoes_novas"] += 1
        for bem in item.get("patrimonio") or []:
            if _upsert_patrimonio(politico.id, bem):
                resumo["patrimonios_novos"] += 1
        for pr in item.get("projetos") or []:
            obj = projetos_por_chave.get(pr.get("chave") or f"{pr.get('casa')}-{pr.get('numero')}-{pr.get('ano')}")
            if obj:
                for coautor in pr.get("coautorias") or []:
                    coautor_slug = coautor.get("slug")
                    coautor_politico = db.session.scalar(select(Politico).where(Politico.slug == coautor_slug)) if coautor_slug else None
                    if coautor_politico is None:
                        raise ErroValidacao("parametro_invalido", "Coautoria referencia político inexistente.")
                    if _upsert_coautoria(obj, coautor_politico.id, coautor):
                        resumo["coautorias_novas"] += 1
        for n in item.get("noticias") or []:
            if _upsert_noticia(politico, n, veiculo):
                resumo["noticias_novas"] += 1
    db.session.commit()
    return {k: v for k, v in resumo.items() if not str(k).startswith("_")}


def importar_arquivo(caminho) -> dict:
    path = Path(caminho)
    if not path.is_file():
        raise ErroValidacao("nao_encontrado", f"Arquivo não encontrado: {path}", 404)
    with path.open(encoding="utf-8") as fh:
        pacote = json.load(fh)
    return importar_pacote(pacote)
