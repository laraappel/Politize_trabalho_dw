from sqlalchemy import func, or_, select

from app.errors import ErroValidacao
from app.extensions import db
from app.models.cargo_eletivo import CargoEletivo
from app.models.dominios_eleitorais_transparencia import Candidatura
from app.models.politico import Politico
from app.paginacao import envelope, pagina


def _texto(args, nome):
    return (args.get(nome) or "").strip() or None


def listar_cargos(args):
    page, per_page = pagina(args)
    base = select(CargoEletivo)

    cargo = _texto(args, "cargo")
    esfera = _texto(args, "esfera")
    partido = _texto(args, "partido")
    uf = (_texto(args, "uf") or "").upper() or None
    municipio = _texto(args, "municipio")
    situacao = _texto(args, "situacao")
    q = _texto(args, "q")
    condicoes_candidatura = (
        Candidatura.politico_id == CargoEletivo.politico_id,
        Candidatura.ano == CargoEletivo.ano_eleicao,
        func.lower(Candidatura.cargo) == func.lower(CargoEletivo.cargo),
        Candidatura.uf.is_not_distinct_from(CargoEletivo.uf),
        Candidatura.municipio.is_not_distinct_from(CargoEletivo.municipio),
        Candidatura.origem_dados == "oficial",
    )
    ano_eleicao = _texto(args, "ano")

    if cargo:
        base = base.where(func.lower(CargoEletivo.cargo) == cargo.lower())
    if esfera:
        base = base.where(CargoEletivo.esfera == esfera.lower())
    if partido:
        base = base.where(func.upper(func.trim(CargoEletivo.partido)) == partido.upper())
    if uf:
        base = base.where(CargoEletivo.uf == uf)
    if municipio:
        base = base.where(CargoEletivo.municipio.ilike(f"%{municipio}%"))
    if situacao:
        base = base.where(func.lower(CargoEletivo.situacao) == situacao.lower())
    if ano_eleicao:
        try:
            base = base.where(CargoEletivo.ano_eleicao == int(ano_eleicao))
        except ValueError:
            raise ErroValidacao("parametro_invalido", "'ano' deve ser um inteiro.")
    if q:
        padrao = f"%{q.replace('%', r'\\%').replace('_', r'\\_')}%"
        numero_filtro = (
            Candidatura.numero_candidatura == q
            if q.isdigit()
            else Candidatura.numero_candidatura.ilike(padrao, escape="\\")
        )
        numero_corresponde = select(Candidatura.id).where(
            *condicoes_candidatura,
            numero_filtro,
        ).exists()
        base = base.join(Politico, Politico.id == CargoEletivo.politico_id).where(or_(
            Politico.nome_completo.ilike(padrao, escape="\\"),
            Politico.nome_urna.ilike(padrao, escape="\\"),
            numero_corresponde,
        ))

    numero_candidatura = (
        select(Candidatura.numero_candidatura)
        .where(
            *condicoes_candidatura,
            Candidatura.numero_candidatura.is_not(None),
        )
        .order_by(Candidatura.id.desc())
        .limit(1)
        .correlate(CargoEletivo)
        .scalar_subquery()
    )

    total = db.session.scalar(select(func.count()).select_from(base.subquery())) or 0
    itens = db.session.execute(
        base.add_columns(numero_candidatura)
        .order_by(CargoEletivo.esfera, CargoEletivo.uf, CargoEletivo.municipio, CargoEletivo.cargo)
        .offset((page - 1) * per_page)
        .limit(per_page)
    ).all()

    payload = []
    for item, numero in itens:
        payload.append({
            "id": item.id,
            "politico_id": item.politico_id,
            "nome": item.politico.nome_exibicao if item.politico else None,
            "cargo": item.cargo,
            "esfera": item.esfera,
            "uf": item.uf,
            "municipio": item.municipio,
            "partido": item.partido,
            "numero_candidato": numero or (item.dados_origem or {}).get("numero_candidato"),
            "ano_eleicao": item.ano_eleicao,
            "ano_inicio": item.ano_inicio,
            "ano_fim": item.ano_fim,
            "situacao": item.situacao,
            "identificador_externo": item.identificador_externo,
            "origem": item.origem,
            "fonte": {"nome": item.fonte_nome, "url": item.fonte_url},
            "coletado_em": item.coletado_em.isoformat() if item.coletado_em else None,
            "atualizado_em": item.atualizado_em.isoformat() if item.atualizado_em else None,
        })

    return envelope(payload, total, page, per_page)


def filtros_cargos():
    cargos = db.session.scalars(
        select(CargoEletivo.cargo).distinct().order_by(CargoEletivo.cargo)
    ).all()
    esferas = db.session.scalars(
        select(CargoEletivo.esfera).distinct().order_by(CargoEletivo.esfera)
    ).all()
    ufs = db.session.scalars(
        select(CargoEletivo.uf).where(CargoEletivo.uf.is_not(None)).distinct().order_by(CargoEletivo.uf)
    ).all()
    municipios = db.session.scalars(
        select(CargoEletivo.municipio).where(CargoEletivo.municipio.is_not(None)).distinct().order_by(CargoEletivo.municipio)
    ).all()
    anos = db.session.scalars(
        select(CargoEletivo.ano_eleicao).where(CargoEletivo.ano_eleicao.is_not(None)).distinct().order_by(CargoEletivo.ano_eleicao.desc())
    ).all()
    partidos = db.session.scalars(
        select(CargoEletivo.partido).where(CargoEletivo.partido.is_not(None)).distinct().order_by(CargoEletivo.partido)
    ).all()
    situacoes = db.session.scalars(
        select(CargoEletivo.situacao).distinct().order_by(CargoEletivo.situacao)
    ).all()
    return {
        "cargos": list(cargos), "esferas": list(esferas), "ufs": list(ufs),
        "municipios": list(municipios), "anos": list(anos),
        "partidos": list(partidos), "situacoes": list(situacoes),
    }
