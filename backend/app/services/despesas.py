"""Consultas e serialização unificada de despesas locais e da Câmara."""
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

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
