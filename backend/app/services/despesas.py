"""Consultas e serialização unificada de despesas locais e da Câmara."""
from decimal import Decimal

from sqlalchemy import case, cast, func, literal, select, union_all
from sqlalchemy.orm import selectinload
from sqlalchemy import Text

from app.extensions import db
from app.models.camara import DespesaCamara
from app.models.dominio import Despesa
from app.models.politico import Politico
from app.paginacao import data_iso
from app.serializacao import dinheiro, iso, origem


def _parametro(args, nome):
    valor = (args.get(nome) or "").strip()
    return valor or None


def _serializar_local(d):
    dados = {
        "id": d.id,
        "categoria": d.categoria,
        "descricao": d.descricao,
        "valor": dinheiro(d.valor),
        "periodo": {
            "inicio": iso(d.periodo_inicio),
            "fim": iso(d.periodo_fim),
        },
        "esfera": d.esfera,
        "politico_id": d.politico_id,
        "politico": None,
    }

    if d.politico is not None:
        dados["politico"] = {
            "id": d.politico.id,
            "nome_exibicao": d.politico.nome_exibicao,
            "uf": d.politico.uf,
            "partido": d.politico.partido,
        }

    dados.update(origem(d))
    return dados


def _serializar_camara(d, politico):
    return {
        "id": f"camara-{d.id}",
        "categoria": d.tipo_despesa,
        "descricao": d.fornecedor or d.tipo_documento,
        "valor": dinheiro(d.valor_documento),
        "valor_liquido": dinheiro(d.valor_liquido),
        "periodo": {
            "inicio": iso(d.data_documento),
            "fim": iso(d.data_documento),
        },
        "esfera": "federal",
        "politico_id": politico.id,
        "politico": {
            "id": politico.id,
            "nome_exibicao": politico.nome_exibicao,
            "uf": politico.uf,
            "partido": politico.partido,
        },
        "demonstracao": False,
        "origem_dados": "camara_deputados",
        "fonte": {
            "nome": "Câmara dos Deputados",
            "url": d.url_documento,
        },
        "id_documento": d.id_documento,
        "tipo_documento": d.tipo_documento,
        "cnpj_cpf_fornecedor": d.cnpj_cpf_fornecedor,
        "ano": d.ano,
        "mes": d.mes,
    }


def listar_despesas_unificadas(args=None, politico_id=None):
    args = args or {}
    categoria = _parametro(args, "categoria")
    uf = _parametro(args, "uf")
    if uf:
        uf = uf.upper()

    de = data_iso(args, "de")
    ate = data_iso(args, "ate")

    if de and ate and de > ate:
        from app.errors import ErroValidacao
        raise ErroValidacao(
            "parametro_invalido",
            "'de' não pode ser posterior a 'ate'.",
        )

    locais = (
        select(Despesa)
        .options(selectinload(Despesa.politico))
    )

    if politico_id is not None:
        locais = locais.where(Despesa.politico_id == politico_id)
    if categoria:
        locais = locais.where(Despesa.categoria == categoria)
    if uf:
        locais = locais.where(
            Despesa.politico_id.in_(
                select(Politico.id).where(func.upper(Politico.uf) == uf)
            )
        )
    if de:
        locais = locais.where(Despesa.periodo_fim >= de)
    if ate:
        locais = locais.where(Despesa.periodo_inicio <= ate)

    registros_locais = db.session.scalars(locais).all()
    resultado = [_serializar_local(d) for d in registros_locais]

    oficiais = (
        select(DespesaCamara, Politico)
        .join(
            Politico,
            Politico.id_camara == DespesaCamara.id_deputado_camara,
        )
    )

    if politico_id is not None:
        oficiais = oficiais.where(Politico.id == politico_id)
    if categoria:
        oficiais = oficiais.where(DespesaCamara.tipo_despesa == categoria)
    if uf:
        oficiais = oficiais.where(func.upper(Politico.uf) == uf)
    if de:
        oficiais = oficiais.where(DespesaCamara.data_documento >= de)
    if ate:
        oficiais = oficiais.where(DespesaCamara.data_documento <= ate)

    registros_oficiais = db.session.execute(oficiais).all()
    resultado.extend(
        _serializar_camara(d, politico)
        for d, politico in registros_oficiais
    )

    resultado.sort(
        key=lambda item: (
            item["periodo"]["inicio"] or "",
            str(item["id"]),
        ),
        reverse=True,
    )
    return resultado


def resumo_financeiro(despesas):
    informados = [
        Decimal(str(item["valor"]))
        for item in despesas
        if item.get("valor") is not None
    ]

    categorias = sorted({
        item.get("categoria") or "Não informada"
        for item in despesas
    })

    por_categoria = []
    for categoria in categorias:
        grupo = [
            item for item in despesas
            if (item.get("categoria") or "Não informada") == categoria
        ]
        valores = [
            Decimal(str(item["valor"]))
            for item in grupo
            if item.get("valor") is not None
        ]

        por_categoria.append({
            "categoria": categoria,
            "registros": len(grupo),
            "registros_sem_valor": len(grupo) - len(valores),
            "soma_valores_informados": dinheiro(
                sum(valores, Decimal("0")) if valores else None
            ),
            "completo": len(valores) == len(grupo),
        })

    return {
        "registros": len(despesas),
        "registros_sem_valor": len(despesas) - len(informados),
        "soma_valores_informados": dinheiro(
            sum(informados, Decimal("0")) if informados else None
        ),
        "completo": bool(despesas) and len(informados) == len(despesas),
        "por_categoria": por_categoria,
    }


def _consulta_unificada_despesas(args=None):
    """Constrói a união SQL já filtrada, evitando carregar todo o histórico em Python."""
    args = args or {}
    categoria = _parametro(args, "categoria")
    uf = _parametro(args, "uf")
    uf = uf.upper() if uf else None
    de = data_iso(args, "de")
    ate = data_iso(args, "ate")

    if de and ate and de > ate:
        from app.errors import ErroValidacao

        raise ErroValidacao("parametro_invalido", "'de' não pode ser posterior a 'ate'.")

    local = (
        select(
            literal("local").label("tipo_registro"),
            Despesa.id.label("id"),
            Despesa.categoria.label("categoria"),
            Despesa.descricao.label("descricao"),
            Despesa.valor.label("valor"),
            Despesa.periodo_inicio.label("inicio"),
            Despesa.periodo_fim.label("fim"),
            Despesa.esfera.label("esfera"),
            Politico.id.label("politico_id"),
            Politico.nome_urna.label("nome_urna"),
            Politico.nome_completo.label("nome_completo"),
            Politico.uf.label("uf"),
            Politico.partido.label("partido"),
            Politico.origem_dados.label("origem_dados"),
            Despesa.fonte_nome.label("fonte_nome"),
            Despesa.fonte_url.label("fonte_url"),
            cast(literal(None), Text).label("id_documento"),
            cast(literal(None), Text).label("tipo_documento"),
            cast(literal(None), Text).label("cnpj_cpf_fornecedor"),
            cast(literal(None), db.Integer).label("ano"),
            cast(literal(None), db.Integer).label("mes"),
            cast(literal(None), Despesa.valor.type).label("valor_liquido"),
        )
        .join(Politico, Politico.id == Despesa.politico_id)
    )
    oficial = (
        select(
            literal("camara").label("tipo_registro"),
            DespesaCamara.id.label("id"),
            DespesaCamara.tipo_despesa.label("categoria"),
            func.coalesce(DespesaCamara.fornecedor, DespesaCamara.tipo_documento).label("descricao"),
            DespesaCamara.valor_documento.label("valor"),
            DespesaCamara.data_documento.label("inicio"),
            DespesaCamara.data_documento.label("fim"),
            literal("federal").label("esfera"),
            Politico.id.label("politico_id"),
            Politico.nome_urna.label("nome_urna"),
            Politico.nome_completo.label("nome_completo"),
            Politico.uf.label("uf"),
            Politico.partido.label("partido"),
            literal("camara_deputados").label("origem_dados"),
            literal("Câmara dos Deputados").label("fonte_nome"),
            DespesaCamara.url_documento.label("fonte_url"),
            DespesaCamara.id_documento.label("id_documento"),
            DespesaCamara.tipo_documento.label("tipo_documento"),
            DespesaCamara.cnpj_cpf_fornecedor.label("cnpj_cpf_fornecedor"),
            DespesaCamara.ano.label("ano"),
            DespesaCamara.mes.label("mes"),
            DespesaCamara.valor_liquido.label("valor_liquido"),
        )
        .join(Politico, Politico.id_camara == DespesaCamara.id_deputado_camara)
    )

    def aplicar_filtros(query, categoria_col, uf_col, inicio_col, fim_col):
        if categoria:
            query = query.where(categoria_col == categoria)
        if uf:
            query = query.where(func.upper(uf_col) == uf)
        if de:
            query = query.where(fim_col >= de)
        if ate:
            query = query.where(inicio_col <= ate)
        return query

    local = aplicar_filtros(local, Despesa.categoria, Politico.uf, Despesa.periodo_inicio, Despesa.periodo_fim)
    oficial = aplicar_filtros(oficial, DespesaCamara.tipo_despesa, Politico.uf, DespesaCamara.data_documento, DespesaCamara.data_documento)
    return union_all(local, oficial).subquery()


def listar_despesas_paginadas(args, page, per_page):
    """Consulta resultados, contagem e totais no banco antes de serializar a página."""
    despesas = _consulta_unificada_despesas(args)
    total, sem_valor, soma = db.session.execute(
        select(
            func.count(),
            func.coalesce(func.sum(case((despesas.c.valor.is_(None), 1), else_=0)), 0),
            func.sum(despesas.c.valor),
        ).select_from(despesas)
    ).one()

    categoria_normalizada = func.coalesce(despesas.c.categoria, literal("Não informada"))
    por_categoria = db.session.execute(
        select(
            categoria_normalizada.label("categoria"),
            func.count().label("registros"),
            func.coalesce(func.sum(case((despesas.c.valor.is_(None), 1), else_=0)), 0).label("sem_valor"),
            func.sum(despesas.c.valor).label("soma"),
        )
        .select_from(despesas)
        .group_by(categoria_normalizada)
        .order_by(categoria_normalizada)
    ).all()

    itens = db.session.execute(
        select(despesas)
        .order_by(despesas.c.inicio.desc().nullslast(), despesas.c.id.desc(), despesas.c.tipo_registro)
        .offset((page - 1) * per_page)
        .limit(per_page)
    ).mappings().all()

    payload = []
    for item in itens:
        politico = {
            "id": item["politico_id"],
            "nome_exibicao": item["nome_urna"] or item["nome_completo"],
            "uf": item["uf"],
            "partido": item["partido"],
        }
        if item["tipo_registro"] == "camara":
            url = item["fonte_url"] or (
                f"https://www.camara.leg.br/cota-parlamentar/nota-fiscal-eletronica?ideDocumentoFiscal={item['id_documento']}"
                if item["id_documento"] else None
            )
            payload.append({
                "id": f"camara-{item['id']}",
                "categoria": item["categoria"],
                "descricao": item["descricao"],
                "valor": dinheiro(item["valor"]),
                "valor_liquido": dinheiro(item["valor_liquido"]),
                "periodo": {"inicio": iso(item["inicio"]), "fim": iso(item["fim"])},
                "esfera": "federal",
                "politico_id": item["politico_id"],
                "politico": politico,
                "demonstracao": False,
                "origem_dados": "camara_deputados",
                "fonte": {"nome": "Câmara dos Deputados", "url": url},
                "id_documento": item["id_documento"],
                "tipo_documento": item["tipo_documento"],
                "cnpj_cpf_fornecedor": item["cnpj_cpf_fornecedor"],
                "ano": item["ano"],
                "mes": item["mes"],
            })
        else:
            payload.append({
                "id": item["id"],
                "categoria": item["categoria"],
                "descricao": item["descricao"],
                "valor": dinheiro(item["valor"]),
                "periodo": {"inicio": iso(item["inicio"]), "fim": iso(item["fim"])},
                "esfera": item["esfera"],
                "politico_id": item["politico_id"],
                "politico": politico,
                "origem_dados": item["origem_dados"] or "demonstracao",
                "demonstracao": (item["origem_dados"] or "demonstracao") == "demonstracao",
                "fonte": {"nome": item["fonte_nome"], "url": item["fonte_url"]}
                if item["fonte_nome"] or item["fonte_url"] else None,
            })

    resumo = {
        "registros": total,
        "registros_sem_valor": sem_valor,
        "soma_valores_informados": dinheiro(soma),
        "completo": bool(total) and sem_valor == 0,
        "por_categoria": [{
            "categoria": row.categoria,
            "registros": row.registros,
            "registros_sem_valor": row.sem_valor,
            "soma_valores_informados": dinheiro(row.soma),
            "completo": row.registros > 0 and row.sem_valor == 0,
        } for row in por_categoria],
    }
    return payload, total, resumo
