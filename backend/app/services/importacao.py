"""Importação idempotente de pacotes JSON (demonstração ou oficiais)."""
import json
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from sqlalchemy import select

from app.dominio_constantes import ESFERAS, ORIGENS, UFS, VOTOS
from app.errors import ErroValidacao
from app.extensions import db
from app.models.dominio import Despesa, Mandato, Projeto, Votacao
from app.models.noticia import Noticia, NoticiaPolitico, Veiculo
from app.models.politico import Politico
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


def _origem(valor, padrao="demonstracao"):
    codigo = (valor or padrao).strip()
    if codigo not in ORIGENS:
        raise ErroValidacao("parametro_invalido", f"origem_dados inválida: {codigo}")
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
    p.origem_dados = _origem(item.get("origem_dados"))
    p.fonte_nome = _texto(item.get("fonte_nome"), 200)
    p.fonte_url = _texto(item.get("fonte_url"))
    db.session.flush()
    return p, novo


def _upsert_mandato(politico_id, item):
    cargo = _texto(item.get("cargo"), 80)
    inicio = _data(item.get("inicio"), "inicio")
    if not cargo or not inicio:
        raise ErroValidacao("parametro_invalido", "Mandato exige cargo e inicio.")
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
    m.fim = _data(item.get("fim"), "fim")
    m.origem_dados = _origem(item.get("origem_dados"))
    m.fonte_nome = _texto(item.get("fonte_nome"), 200)
    m.fonte_url = _texto(item.get("fonte_url"))
    if existente is None:
        db.session.add(m)
    return existente is None


def _upsert_projeto(politico_id, item) -> tuple[Projeto, bool]:
    casa = (_texto(item.get("casa"), 30) or "").lower()
    numero, ano = item.get("numero"), item.get("ano")
    if not casa or numero is None or ano is None:
        raise ErroValidacao("parametro_invalido", "Projeto exige casa, numero e ano.")
    existente = db.session.scalar(
        select(Projeto).where(Projeto.casa == casa, Projeto.numero == int(numero), Projeto.ano == int(ano))
    )
    pr = existente or Projeto(casa=casa, numero=int(numero), ano=int(ano))
    pr.politico_id = politico_id
    pr.ementa = _texto(item.get("ementa"))
    pr.situacao = _texto(item.get("situacao"), 40)
    pr.data_apresentacao = _data(item.get("data_apresentacao"), "data_apresentacao")
    pr.url_oficial = _texto(item.get("url_oficial"))
    pr.origem_dados = _origem(item.get("origem_dados"))
    pr.fonte_nome = _texto(item.get("fonte_nome"), 200)
    pr.fonte_url = _texto(item.get("fonte_url"))
    if existente is None:
        db.session.add(pr)
        db.session.flush()
    return pr, existente is None


def _upsert_votacao(politico_id, item, projetos_por_chave: dict):
    ident = _texto(item.get("identificador_externo"), 80)
    casa = _texto(item.get("casa"), 30)
    if not ident or not casa:
        raise ErroValidacao("parametro_invalido", "Votação exige identificador_externo e casa.")
    voto = item.get("voto")
    if voto in ("", None):
        voto = None
    elif voto not in VOTOS:
        raise ErroValidacao("parametro_invalido", f"Voto inválido: {voto}")
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
    v.origem_dados = _origem(item.get("origem_dados"))
    v.fonte_nome = _texto(item.get("fonte_nome"), 200)
    v.fonte_url = _texto(item.get("fonte_url"))
    chave_proj = item.get("projeto")
    if chave_proj:
        pr = projetos_por_chave.get(chave_proj)
        v.projeto_id = pr.id if pr else None
    if existente is None:
        db.session.add(v)
    return existente is None


def _upsert_despesa(politico_id, item):
    categoria = _texto(item.get("categoria"), 80)
    descricao = _texto(item.get("descricao"))
    inicio = _data(item.get("periodo_inicio") or (item.get("periodo") or {}).get("inicio"), "periodo_inicio")
    fim = _data(item.get("periodo_fim") or (item.get("periodo") or {}).get("fim"), "periodo_fim")
    if not categoria or not descricao or not inicio or not fim:
        raise ErroValidacao("parametro_invalido", "Despesa exige categoria, descricao e período.")
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
    d.origem_dados = _origem(item.get("origem_dados"))
    d.fonte_nome = _texto(item.get("fonte_nome"), 200)
    d.fonte_url = _texto(item.get("fonte_url"))
    if existente is None:
        db.session.add(d)
    return existente is None


def _upsert_noticia(politico: Politico, item, veiculo: Veiculo):
    url = _texto(item.get("url_original"))
    titulo = _texto(item.get("titulo_original"))
    if not url or not titulo:
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
