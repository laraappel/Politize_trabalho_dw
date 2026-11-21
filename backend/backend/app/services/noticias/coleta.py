"""Orquestra a coleta: fonte -> deduplicação -> associação -> persistência."""
import os
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.extensions import db
from app.models.noticia import (
    ColetaNoticias,
    Noticia,
    NoticiaAtualizacao,
    NoticiaPolitico,
    Veiculo,
)
from app.services.noticias.associacao import AssociadorPoliticos
from app.services.noticias.classificacao import classificar_natureza
from app.services.noticias.fontes import todas_as_fontes
from app.services.noticias.fontes.base import ErroColeta, FonteNaoAutorizada, FonteNoticias, ItemBruto
from app.services.noticias.normalizacao import canonicalizar_url, chave_dedup, slugify
from app.services.noticias.politicos_repo import carregar_politicos


def _agora():
    return datetime.now(timezone.utc)


def sincronizar_veiculos(fontes: dict[str, FonteNoticias] | None = None) -> dict[str, Veiculo]:
    """Garante uma linha em `veiculos` por fonte, com a base de autorização registrada."""
    fontes = fontes or todas_as_fontes()
    resultado = {}
    for slug, f in fontes.items():
        v = db.session.scalar(select(Veiculo).where(Veiculo.slug == slug))
        if v is None:
            v = Veiculo(slug=slug)
            db.session.add(v)
        v.nome, v.dominio, v.tipo = f.nome, f.dominio, f.tipo
        v.coleta_autorizada, v.permite_resumo = f.autorizada, f.permite_resumo
        v.base_autorizacao, v.url_termos = f.base_autorizacao, f.url_termos
        resultado[slug] = v
    db.session.commit()
    return resultado


def _assunto(item: ItemBruto) -> tuple[str | None, str | None]:
    if item.assunto_padrao:
        return item.assunto_padrao
    if item.categorias:
        return slugify(item.categorias[0]), item.categorias[0]
    return None, None


def _aplicar_associacoes(noticia: Noticia, candidatas) -> None:
    existentes = {a.politico_id: a for a in noticia.associacoes}
    for c in candidatas:
        atual = existentes.get(c.politico_id)
        if atual is not None:
            # nunca sobrescreve revisão manual nem associação rejeitada
            continue
        noticia.associacoes.append(
            NoticiaPolitico(
                politico_id=c.politico_id,
                status=c.status,
                grau_confirmacao=c.grau,
                metodo=c.metodo,
                origem="automatica",
                evidencias=c.evidencias,
            )
        )


def _localizar_existente(veiculo: Veiculo, item: ItemBruto, url_canonica: str, chave: str) -> Noticia | None:
    cond = [Noticia.url_canonica == url_canonica, Noticia.chave_dedup == chave]
    consulta = select(Noticia).where(db.or_(*cond))
    if item.guid:
        consulta = select(Noticia).where(
            db.or_(*cond, db.and_(Noticia.veiculo_id == veiculo.id, Noticia.guid_origem == item.guid))
        )
    return db.session.scalars(consulta).first()


def processar_item(veiculo: Veiculo, associador: AssociadorPoliticos, item: ItemBruto) -> str:
    """Retorna 'novo', 'atualizado', 'inalterado' ou 'descartado'."""
    candidatas = associador.associar(item.titulo, item.resumo, item.links_html)
    url_canonica = canonicalizar_url(item.url)
    chave = chave_dedup(veiculo.slug, item.titulo, item.publicado_em)
    existente = _localizar_existente(veiculo, item, url_canonica, chave)

    if existente is None:
        if not candidatas:
            return "descartado"  # sem vínculo com nenhum político cadastrado: não armazenamos
        slug_assunto, nome_assunto = _assunto(item)
        noticia = Noticia(
            veiculo_id=veiculo.id,
            url_original=item.url,
            url_canonica=url_canonica,
            guid_origem=item.guid,
            chave_dedup=chave,
            titulo_original=item.titulo,
            resumo=item.resumo if veiculo.permite_resumo else None,
            publicado_em=item.publicado_em,
            assunto_slug=slug_assunto,
            assunto_nome=nome_assunto,
            natureza=classificar_natureza(item.titulo, item.resumo),
            natureza_origem="heuristica",
        )
        db.session.add(noticia)
        _aplicar_associacoes(noticia, candidatas)
        db.session.flush()
        return "novo"

    mudou = False
    if existente.titulo_original != item.titulo:
        db.session.add(
            NoticiaAtualizacao(
                noticia_id=existente.id,
                tipo="alteracao_titulo",
                descricao=f"Título alterado pelo veículo. Anterior: {existente.titulo_original}",
                url_referencia=existente.url_original,
                criado_por="sistema",
            )
        )
        existente.titulo_original = item.titulo
        mudou = True
    antes = len(existente.associacoes)
    _aplicar_associacoes(existente, candidatas)
    if len(existente.associacoes) != antes:
        mudou = True
    if mudou:
        existente.atualizado_em = _agora()
        db.session.flush()
        return "atualizado"
    return "inalterado"


def coletar_fonte(slug: str, forcar: bool = False, fontes: dict[str, FonteNoticias] | None = None) -> ColetaNoticias:
    fontes = fontes or todas_as_fontes()
    if slug not in fontes:
        raise KeyError(f"Fonte desconhecida: {slug}")
    fonte = fontes[slug]
    veiculo = sincronizar_veiculos({slug: fonte})[slug]

    coleta = ColetaNoticias(veiculo_id=veiculo.id, status="em_andamento")
    db.session.add(coleta)
    db.session.commit()

    def encerrar(status, mensagem=None):
        coleta.status, coleta.mensagem, coleta.finalizada_em = status, mensagem, _agora()
        db.session.commit()
        return coleta

    if not fonte.autorizada:
        return encerrar("ignorada", f"Fonte sem acesso autorizado: {fonte.base_autorizacao}")

    intervalo = int(os.getenv("NOTICIAS_INTERVALO_MIN_SEGUNDOS", "900"))
    if not forcar and veiculo.ultima_coleta_em and _agora() - veiculo.ultima_coleta_em < timedelta(seconds=intervalo):
        return encerrar("ignorada", f"Última coleta há menos de {intervalo}s; respeitando intervalo mínimo.")

    try:
        itens = fonte.coletar()
    except (FonteNaoAutorizada, ErroColeta) as exc:
        db.session.rollback()
        return encerrar("erro", str(exc))

    politicos = carregar_politicos()
    if not politicos:
        veiculo.ultima_coleta_em = _agora()
        coleta.itens_lidos = len(itens)
        return encerrar("ok", "Nenhum político cadastrado: nada foi associado nem armazenado.")

    associador = AssociadorPoliticos(politicos)
    contagem = {"novo": 0, "atualizado": 0, "inalterado": 0, "descartado": 0}
    for item in itens:
        try:
            with db.session.begin_nested():
                contagem[processar_item(veiculo, associador, item)] += 1
        except Exception as exc:  # um item ruim não derruba a coleta
            contagem["descartado"] += 1
            coleta.mensagem = f"Erro em item {item.url}: {exc}"[:500]
    veiculo.ultima_coleta_em = _agora()
    coleta.itens_lidos = len(itens)
    coleta.itens_novos = contagem["novo"]
    coleta.itens_atualizados = contagem["atualizado"]
    coleta.itens_descartados = contagem["descartado"]
    return encerrar("ok", coleta.mensagem)
