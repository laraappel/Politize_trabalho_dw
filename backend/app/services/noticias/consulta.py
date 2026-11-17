"""Consultas públicas e operações editoriais sobre notícias."""
import hmac
import os
import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import exists, func, select
from sqlalchemy.orm import selectinload

from app.errors import ErroValidacao
from app.extensions import db
from app.models.noticia import (
    Noticia,
    NoticiaAtualizacao,
    NoticiaPolitico,
    PoliticoRef,
    Veiculo,
)
from app.services.noticias.classificacao import AVISOS, NATUREZAS, ROTULOS

BRT = timezone(timedelta(hours=-3))  # Brasil sem horário de verão desde 2019
PER_PAGE_PADRAO, PER_PAGE_MAX = 10, 50
GRAUS = {"alta": "Alta", "media": "Média", "baixa": "Baixa", "manual": "Revisão manual"}


@dataclass
class Filtros:
    politico: int | None = None
    veiculo: str | None = None
    assunto: str | None = None
    natureza: str | None = None
    de: date | None = None
    ate: date | None = None
    ordem: str = "recentes"
    page: int = 1
    per_page: int = PER_PAGE_PADRAO


def _int(args, nome, minimo=1, maximo=None):
    bruto = args.get(nome)
    if bruto in (None, ""):
        return None
    try:
        v = int(bruto)
    except ValueError:
        raise ErroValidacao("parametro_invalido", f"'{nome}' deve ser um inteiro.")
    if v < minimo or (maximo and v > maximo):
        raise ErroValidacao("parametro_invalido", f"'{nome}' fora do intervalo permitido.")
    return v


def _data(args, nome):
    bruto = args.get(nome)
    if not bruto:
        return None
    try:
        return date.fromisoformat(bruto)
    except ValueError:
        raise ErroValidacao("parametro_invalido", f"'{nome}' deve estar no formato AAAA-MM-DD.")


def parse_filtros(args) -> Filtros:
    f = Filtros(
        politico=_int(args, "politico"),
        veiculo=(args.get("veiculo") or None),
        assunto=(args.get("assunto") or None),
        natureza=(args.get("natureza") or None),
        de=_data(args, "de"),
        ate=_data(args, "ate"),
        ordem=args.get("ordem", "recentes"),
        page=_int(args, "page") or 1,
        per_page=_int(args, "per_page", maximo=PER_PAGE_MAX) or PER_PAGE_PADRAO,
    )
    if f.ordem not in ("recentes", "antigas"):
        raise ErroValidacao("parametro_invalido", "'ordem' deve ser 'recentes' ou 'antigas'.")
    if f.natureza and f.natureza not in NATUREZAS:
        raise ErroValidacao("parametro_invalido", "'natureza' desconhecida.")
    if f.de and f.ate and f.de > f.ate:
        raise ErroValidacao("parametro_invalido", "'de' não pode ser posterior a 'ate'.")
    return f


def _confirmada():
    return NoticiaPolitico.status == "confirmada"


def _consulta_base(f: Filtros):
    cond = [
        exists().where(NoticiaPolitico.noticia_id == Noticia.id, _confirmada(),
                       *( [NoticiaPolitico.politico_id == f.politico] if f.politico else [] ))
    ]
    if f.veiculo:
        cond.append(Noticia.veiculo_id.in_(select(Veiculo.id).where(Veiculo.slug == f.veiculo)))
    if f.assunto:
        cond.append(Noticia.assunto_slug == f.assunto)
    if f.natureza:
        cond.append(Noticia.natureza == f.natureza)
    if f.de:
        cond.append(Noticia.publicado_em >= datetime.combine(f.de, time.min, tzinfo=BRT))
    if f.ate:
        cond.append(Noticia.publicado_em < datetime.combine(f.ate + timedelta(days=1), time.min, tzinfo=BRT))
    return select(Noticia).where(*cond)


def _iso(dt):
    return dt.isoformat() if dt else None


def serializar(n: Noticia, detalhe: bool = False) -> dict:
    publicas = [a for a in n.associacoes if a.status == "confirmada"]
    dados = {
        "id": n.id,
        "titulo_original": n.titulo_original,
        "url_original": n.url_original,
        "veiculo": {"slug": n.veiculo.slug, "nome": n.veiculo.nome, "tipo": n.veiculo.tipo},
        "publicado_em": _iso(n.publicado_em),
        "resumo": n.resumo,
        "assunto": {"slug": n.assunto_slug, "nome": n.assunto_nome} if n.assunto_slug else None,
        "natureza": {
            "codigo": n.natureza,
            "rotulo": ROTULOS[n.natureza],
            "aviso": AVISOS[n.natureza],
            "origem": n.natureza_origem,
        },
        "politicos": [
            {
                "id": a.politico_id,
                "nome": a.politico.nome_exibicao,
                "grau_confirmacao": a.grau_confirmacao,
                "metodo": a.metodo,
                "origem": a.origem,
                **({"evidencias": a.evidencias} if detalhe else {}),
            }
            for a in publicas
        ],
        "total_atualizacoes": len(n.atualizacoes),
    }
    if detalhe:
        dados["atualizacoes"] = [serializar_atualizacao(a) for a in n.atualizacoes]
        dados["coletado_em"] = _iso(n.coletado_em)
        dados["atualizado_em"] = _iso(n.atualizado_em)
    return dados


def serializar_atualizacao(a: NoticiaAtualizacao) -> dict:
    return {
        "id": a.id,
        "tipo": a.tipo,
        "descricao": a.descricao,
        "url_referencia": a.url_referencia,
        "noticia_relacionada_id": a.noticia_relacionada_id,
        "criado_por": a.criado_por,
        "criado_em": _iso(a.criado_em),
    }


def listar_noticias(f: Filtros) -> dict:
    base = _consulta_base(f)
    total = db.session.scalar(select(func.count()).select_from(base.subquery()))
    ordem = (
        (Noticia.publicado_em.desc().nulls_last(), Noticia.id.desc())
        if f.ordem == "recentes"
        else (Noticia.publicado_em.asc().nulls_last(), Noticia.id.asc())
    )
    itens = db.session.scalars(
        base.order_by(*ordem)
        .limit(f.per_page)
        .offset((f.page - 1) * f.per_page)
        .options(
            selectinload(Noticia.veiculo),
            selectinload(Noticia.atualizacoes),
            selectinload(Noticia.associacoes).selectinload(NoticiaPolitico.politico),
        )
    ).all()
    return {
        "items": [serializar(n) for n in itens],
        "total": total,
        "page": f.page,
        "per_page": f.per_page,
        "pages": max(1, -(-total // f.per_page)),
    }


def obter_noticia(noticia_id: int) -> dict | None:
    n = db.session.get(Noticia, noticia_id)
    if n is None or not any(a.status == "confirmada" for a in n.associacoes):
        return None
    return serializar(n, detalhe=True)


def politico_existe(politico_id: int) -> bool:
    return db.session.get(PoliticoRef, politico_id) is not None


def listar_filtros() -> dict:
    publica = exists().where(NoticiaPolitico.noticia_id == Noticia.id, _confirmada())
    veiculos = db.session.execute(
        select(Veiculo.slug, Veiculo.nome)
        .where(Veiculo.id.in_(select(Noticia.veiculo_id).where(publica)))
        .order_by(Veiculo.nome)
    ).all()
    assuntos = db.session.execute(
        select(Noticia.assunto_slug, Noticia.assunto_nome)
        .where(publica, Noticia.assunto_slug.is_not(None))
        .distinct()
        .order_by(Noticia.assunto_nome)
    ).all()
    politicos = db.session.execute(
        select(PoliticoRef.id, PoliticoRef.nome_urna, PoliticoRef.nome_completo)
        .where(PoliticoRef.id.in_(select(NoticiaPolitico.politico_id).where(_confirmada())))
        .order_by(PoliticoRef.nome_completo)
    ).all()
    return {
        "veiculos": [{"slug": s, "nome": n} for s, n in veiculos],
        "assuntos": [{"slug": s, "nome": n} for s, n in assuntos],
        "politicos": [{"id": i, "nome": urna or comp} for i, urna, comp in politicos],
        "naturezas": [{"codigo": c, "rotulo": ROTULOS[c]} for c in NATUREZAS],
    }


def listar_veiculos() -> list[dict]:
    return [
        {
            "slug": v.slug,
            "nome": v.nome,
            "dominio": v.dominio,
            "tipo": v.tipo,
            "coleta_autorizada": v.coleta_autorizada,
            "base_autorizacao": v.base_autorizacao,
            "url_termos": v.url_termos,
            "ultima_coleta_em": _iso(v.ultima_coleta_em),
        }
        for v in db.session.scalars(select(Veiculo).order_by(Veiculo.nome))
    ]


# --------------------------- operações editoriais ---------------------------
def admin_autorizado(token: str | None) -> bool:
    esperado = os.getenv("ADMIN_TOKEN", "")
    return bool(esperado) and bool(token) and hmac.compare_digest(token, esperado)


def _url_http(valor):
    if valor in (None, ""):
        return None
    if not re.match(r"^https?://", valor):
        raise ErroValidacao("parametro_invalido", "'url_referencia' deve começar com http:// ou https://.")
    return valor


def adicionar_atualizacao(noticia_id: int, dados: dict) -> dict:
    n = db.session.get(Noticia, noticia_id)
    if n is None:
        raise ErroValidacao("nao_encontrado", "Notícia não encontrada.", 404)
    tipo = dados.get("tipo")
    if tipo not in ("desdobramento", "correcao", "complemento"):
        raise ErroValidacao("parametro_invalido", "'tipo' deve ser desdobramento, correcao ou complemento.")
    descricao = (dados.get("descricao") or "").strip()
    if not descricao:
        raise ErroValidacao("parametro_invalido", "'descricao' é obrigatória.")
    relacionada = dados.get("noticia_relacionada_id")
    if relacionada is not None and db.session.get(Noticia, relacionada) is None:
        raise ErroValidacao("parametro_invalido", "'noticia_relacionada_id' não existe.")
    a = NoticiaAtualizacao(
        noticia_id=noticia_id,
        tipo=tipo,
        descricao=descricao[:2000],
        url_referencia=_url_http(dados.get("url_referencia")),
        noticia_relacionada_id=relacionada,
        criado_por=(dados.get("criado_por") or "editor")[:80],
    )
    db.session.add(a)
    n.atualizado_em = datetime.now(timezone.utc)
    db.session.commit()
    return serializar_atualizacao(a)


def revisar_associacao(noticia_id: int, politico_id: int, dados: dict) -> dict:
    n = db.session.get(Noticia, noticia_id)
    if n is None or not politico_existe(politico_id):
        raise ErroValidacao("nao_encontrado", "Notícia ou político não encontrado.", 404)
    decisao = dados.get("decisao")
    if decisao not in ("confirmar", "rejeitar"):
        raise ErroValidacao("parametro_invalido", "'decisao' deve ser confirmar ou rejeitar.")
    revisor = (dados.get("revisado_por") or "").strip()
    if not revisor:
        raise ErroValidacao("parametro_invalido", "'revisado_por' é obrigatório para rastreabilidade.")
    a = db.session.get(NoticiaPolitico, (noticia_id, politico_id))
    if a is None:
        a = NoticiaPolitico(noticia_id=noticia_id, politico_id=politico_id, metodo="revisao_manual", evidencias=[])
        db.session.add(a)
    a.status = "confirmada" if decisao == "confirmar" else "rejeitada"
    a.grau_confirmacao, a.origem = "manual", "manual"
    a.revisado_por, a.revisado_em = revisor[:80], datetime.now(timezone.utc)
    db.session.commit()
    return {"noticia_id": noticia_id, "politico_id": politico_id, "status": a.status}


def reclassificar_natureza(noticia_id: int, dados: dict) -> dict:
    n = db.session.get(Noticia, noticia_id)
    if n is None:
        raise ErroValidacao("nao_encontrado", "Notícia não encontrada.", 404)
    if dados.get("natureza") not in NATUREZAS:
        raise ErroValidacao("parametro_invalido", "'natureza' desconhecida.")
    n.natureza, n.natureza_origem = dados["natureza"], "editorial"
    db.session.commit()
    return {"id": n.id, "natureza": n.natureza, "origem": n.natureza_origem}


def listar_pendentes(page: int = 1, per_page: int = 20) -> dict:
    base = select(NoticiaPolitico).where(NoticiaPolitico.status == "pendente_revisao")
    total = db.session.scalar(select(func.count()).select_from(base.subquery()))
    linhas = db.session.scalars(
        base.order_by(NoticiaPolitico.criado_em.desc()).limit(per_page).offset((page - 1) * per_page)
    ).all()
    return {
        "items": [
            {
                "noticia_id": a.noticia_id,
                "titulo_original": a.noticia.titulo_original,
                "url_original": a.noticia.url_original,
                "politico": {"id": a.politico_id, "nome": a.politico.nome_exibicao},
                "grau_confirmacao": a.grau_confirmacao,
                "metodo": a.metodo,
                "evidencias": a.evidencias,
            }
            for a in linhas
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
    }
