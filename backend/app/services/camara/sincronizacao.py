
"""Importação idempotente dos dados públicos da Câmara para o PostgreSQL."""

import hashlib
import json
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation

from sqlalchemy import select

from app.adapters.camara.client import CamaraClient
from app.extensions import db
from app.models.politico import Politico as PoliticoRef
from app.models.dominio import Votacao
from app.models.camara import (
    DataSyncLog,
    DespesaCamara,
    HistoricoCamara,
    MandatoCamara,
    PartidoCamara,
    ProposicaoCamara,
)

FONTE = "camara_deputados"


def _data(valor):
    if not valor:
        return None
    try:
        return date.fromisoformat(str(valor)[:10])
    except (TypeError, ValueError):
        return None


def _data_hora(valor):
    if not valor:
        return None
    try:
        texto = str(valor).replace("Z", "+00:00")
        resultado = datetime.fromisoformat(texto)
        if resultado.tzinfo is None:
            resultado = resultado.replace(tzinfo=timezone.utc)
        else:
            resultado = resultado.astimezone(timezone.utc)
        return resultado
    except (TypeError, ValueError):
        return None


def _decimal(valor):
    if valor is None or valor == "":
        return None
    try:
        return Decimal(str(valor))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _json_chave(dados):
    serializado = json.dumps(
        dados, ensure_ascii=False, sort_keys=True, default=str
    )
    return hashlib.sha256(serializado.encode("utf-8")).hexdigest()


def _atualizar_campos(objeto, campos):
    """Atualiza somente campos fornecidos e registra alterações reais."""
    alterou = False

    for nome, valor in campos.items():
        if valor is None:
            continue
        atual = getattr(objeto, nome)
        if isinstance(atual, datetime) and isinstance(valor, datetime):
            if atual.tzinfo is None:
                atual = atual.replace(tzinfo=timezone.utc)
            if valor.tzinfo is None:
                valor = valor.replace(tzinfo=timezone.utc)
        if atual != valor:
            setattr(objeto, nome, valor)
            alterou = True

    if alterou:
        objeto.atualizado_em = datetime.now(timezone.utc)

    return alterou


def _iniciar_log(entidade, operacao):
    log = DataSyncLog(
        fonte=FONTE,
        entidade=entidade,
        operacao=operacao,
        status="em_andamento",
    )
    db.session.add(log)
    db.session.commit()
    return log


def _finalizar_log(log, lidos, novos, atualizados, erro=None):
    log.registros_lidos = lidos
    log.registros_novos = novos
    log.registros_atualizados = atualizados
    log.status = (
        "erro" if erro else
        ("ok" if novos or atualizados else "sem_alteracao")
    )
    log.mensagem = str(erro)[:4000] if erro else None
    log.finalizada_em = datetime.now(timezone.utc)
    db.session.commit()


def _executar_log(entidade, operacao, funcao):
    log = _iniciar_log(entidade, operacao)

    try:
        resultado = funcao()
        _finalizar_log(log, *resultado)
        return resultado
    except Exception as exc:
        db.session.rollback()
        log = db.session.get(DataSyncLog, log.id)
        _finalizar_log(log, 0, 0, 0, erro=exc)
        raise


class CamaraSyncService:

    def __init__(self, client=None):
        self.client = client or CamaraClient()

    def sincronizar_partidos(self, operacao="atualizacao"):
        def importar():
            lidos = novos = atualizados = 0

            for item in self.client.listar("partidos", itens=100):
                sigla = item.get("sigla")
                if not sigla:
                    continue

                lidos += 1

                partido = db.session.execute(
                    select(PartidoCamara).where(
                        PartidoCamara.sigla == sigla
                    )
                ).scalar_one_or_none()

                campos = {
                    "id_partido_camara": item.get("id"),
                    "nome": item.get("nome"),
                    "uri_origem": item.get("uri"),
                    "origem": FONTE,
                    "dados_origem": item,
                }

                if partido is None:
                    db.session.add(
                        PartidoCamara(sigla=sigla, **campos)
                    )
                    novos += 1
                elif _atualizar_campos(partido, campos):
                    atualizados += 1

                db.session.commit()

            return lidos, novos, atualizados

        return _executar_log("partidos", operacao, importar)

    def sincronizar_deputados(
        self, operacao="atualizacao", limite=None
    ):
        def importar():
            lidos = novos = atualizados = 0

            for item in self.client.listar("deputados", itens=100):
                if limite is not None and lidos >= limite:
                    break

                id_camara = item.get("id")
                if not id_camara:
                    continue

                lidos += 1

                detalhe = (
                    self.client.get(f"deputados/{id_camara}").get("dados")
                    or {}
                )
                status = detalhe.get("ultimoStatus") or {}

                nome = detalhe.get("nomeCivil") or item.get("nome")
                if not nome:
                    continue

                id_camara = int(id_camara)

                politico = db.session.execute(
                    select(PoliticoRef).where(
                        PoliticoRef.id_camara == id_camara
                    )
                ).scalar_one_or_none()

                sigla = (
                    status.get("siglaPartido")
                    or item.get("siglaPartido")
                )

                agora = datetime.now(timezone.utc)

                campos = {
                    "nome_completo": detalhe.get("nomeCivil") or nome,
                    "nome_urna": item.get("nome"),
                    "cargo": "Deputado federal",
                    "uf": status.get("siglaUf") or item.get("siglaUf"),
                    "partido": sigla,
                    "id_camara": id_camara,
                    "origem_dados": "oficial",
                    "fonte_nome": "Câmara dos Deputados",
                    "fonte_url": detalhe.get("uri") or item.get("uri"),
                    "dados_camara": detalhe,
                }

                if politico is None:
                    politico = PoliticoRef(
                        slug=f"deputado-federal-{id_camara}",
                        coletado_em=agora,
                        atualizado_em=agora,
                        **campos,
                    )
                    db.session.add(politico)
                    novos += 1
                elif _atualizar_campos(politico, campos):
                    atualizados += 1

                politico.coletado_em = agora
                db.session.flush()

                if sigla:
                    partido = db.session.execute(
                        select(PartidoCamara).where(
                            PartidoCamara.sigla == sigla
                        )
                    ).scalar_one_or_none()

                    if partido is None:
                        db.session.add(
                            PartidoCamara(
                                sigla=sigla,
                                origem=FONTE,
                                dados_origem={"sigla": sigla},
                            )
                        )

                db.session.commit()

            return lidos, novos, atualizados

        return _executar_log("deputados", operacao, importar)

    def sincronizar_mandatos(
        self, operacao="atualizacao", limite_deputados=None
    ):
        """Sincroniza eventos do endpoint /historico sem tratá-los como mandatos."""

        def importar():
            lidos = novos = atualizados = 0

            politicos = db.session.execute(
                select(PoliticoRef)
                .where(PoliticoRef.id_camara.is_not(None))
                .order_by(PoliticoRef.id_camara.asc())
            ).scalars().all()

            if limite_deputados is not None:
                politicos = politicos[:limite_deputados]

            for politico in politicos:
                corpo = self.client.get(
                    f"deputados/{politico.id_camara}/historico"
                )
                dados = corpo.get("dados") or []

                if isinstance(dados, dict):
                    dados = (
                        dados.get("historico", [])
                        or dados.get("itens", [])
                    )

                for item in dados:
                    if not isinstance(item, dict):
                        continue

                    lidos += 1
                    chave = (
                        f"historico:{politico.id_camara}:"
                        f"{_json_chave(item)}"
                    )

                    registro = db.session.execute(
                        select(HistoricoCamara).where(
                            HistoricoCamara.chave_origem == chave
                        )
                    ).scalar_one_or_none()

                    campos = {
                        "politico_id": politico.id,
                        "id_deputado_camara": politico.id_camara,
                        "id_legislatura": item.get("idLegislatura"),
                        "nome": item.get("nome"),
                        "nome_eleitoral": item.get("nomeEleitoral"),
                        "sigla_partido": item.get("siglaPartido"),
                        "sigla_uf": item.get("siglaUf"),
                        "email": item.get("email"),
                        "url_foto": item.get("urlFoto"),
                        "data_hora": _data_hora(item.get("dataHora")),
                        "situacao": item.get("situacao"),
                        "condicao_eleitoral": item.get("condicaoEleitoral"),
                        "descricao_status": item.get("descricaoStatus"),
                        "uri_origem": item.get("uri"),
                        "origem": FONTE,
                        "dados_origem": item,
                    }

                    if registro is None:
                        db.session.add(
                            HistoricoCamara(
                                chave_origem=chave,
                                **campos,
                            )
                        )
                        novos += 1
                    elif _atualizar_campos(registro, campos):
                        atualizados += 1

                db.session.commit()

            return lidos, novos, atualizados

        return _executar_log("historico_deputados", operacao, importar)

    def sincronizar_despesas(
        self, anos, operacao="atualizacao", limite_deputados=None
    ):
        def importar():
            lidos = novos = atualizados = 0

            politicos = db.session.execute(
                select(PoliticoRef)
                .where(PoliticoRef.id_camara.is_not(None))
                .order_by(PoliticoRef.id_camara.asc())
            ).scalars().all()

            if limite_deputados is not None:
                politicos = politicos[:limite_deputados]

            for politico in politicos:
                for ano in anos:
                    despesas = self.client.listar(
                        f"deputados/{politico.id_camara}/despesas",
                        params={"ano": int(ano)},
                        itens=100,
                    )

                    for item in despesas:
                        lidos += 1

                        id_documento = item.get("codDocumento")

                        if id_documento is not None:
                            id_documento = str(id_documento)

                        chave = (
                            f"hash:{politico.id_camara}:"
                            f"{_json_chave(item)}"
                        )

                        despesa = db.session.execute(
                            select(DespesaCamara).where(
                                DespesaCamara.chave_origem == chave
                            )
                        ).scalar_one_or_none()

                        campos = {
                            "id_deputado_camara": politico.id_camara,
                            "id_documento": id_documento,
                            "ano": item.get("ano") or int(ano),
                            "mes": item.get("mes"),
                            "tipo_despesa": item.get("tipoDespesa"),
                            "tipo_documento": item.get("tipoDocumento"),
                            "data_documento": _data(
                                item.get("dataDocumento")
                            ),
                            "fornecedor": item.get("nomeFornecedor"),
                            "cnpj_cpf_fornecedor": item.get(
                                "cnpjCpfFornecedor"
                            ),
                            "valor_documento": _decimal(
                                item.get("valorDocumento")
                            ),
                            "valor_liquido": _decimal(
                                item.get("valorLiquido")
                            ),
                            "url_documento": item.get("urlDocumento"),
                            "origem": FONTE,
                            "dados_origem": item,
                        }

                        if despesa is None:
                            db.session.add(
                                DespesaCamara(
                                    chave_origem=chave,
                                    **campos,
                                )
                            )
                            novos += 1
                        elif _atualizar_campos(despesa, campos):
                            atualizados += 1

                    db.session.commit()

            return lidos, novos, atualizados

        return _executar_log("despesas", operacao, importar)

    def sincronizar_proposicoes(
        self, anos, operacao="atualizacao", limite=None
    ):
        def importar():
            lidos = novos = atualizados = 0

            for ano in anos:
                if limite is not None and lidos >= limite:
                    break

                proposicoes = self.client.listar(
                    "proposicoes",
                    params={"ano": int(ano)},
                    itens=100,
                )

                for item in proposicoes:
                    if limite is not None and lidos >= limite:
                        break

                    id_prop = item.get("id")
                    if id_prop is None:
                        continue

                    lidos += 1

                    prop = db.session.execute(
                        select(ProposicaoCamara).where(
                            ProposicaoCamara.id_proposicao_camara
                            == int(id_prop)
                        )
                    ).scalar_one_or_none()

                    status = item.get("statusProposicao") or {}

                    campos = {
                        "id_proposicao_camara": int(id_prop),
                        "uri_origem": item.get("uri"),
                        "sigla_tipo": item.get("siglaTipo"),
                        "numero": item.get("numero"),
                        "ano": item.get("ano") or int(ano),
                        "ementa": item.get("ementa"),
                        "data_apresentacao": _data(
                            item.get("dataApresentacao")
                        ),
                        "uri_orgao_numerador": item.get(
                            "uriOrgaoNumerador"
                        ),
                        "status_descricao": status.get(
                            "descricaoSituacao"
                        ),
                        "status_data_hora": _data_hora(
                            status.get("dataHora")
                        ),
                        "origem": FONTE,
                        "dados_origem": item,
                    }

                    if prop is None:
                        db.session.add(
                            ProposicaoCamara(**campos)
                        )
                        novos += 1
                    elif _atualizar_campos(prop, campos):
                        atualizados += 1

                db.session.commit()

            return lidos, novos, atualizados

        return _executar_log("proposicoes", operacao, importar)

    def sincronizar_votacoes(
        self, ano, operacao="atualizacao", limite_deputados=None
    ):
        """Importa os votos individuais dos deputados nas votações do Plenário."""

        def importar():
            lidos = novos = atualizados = 0

            politicos = db.session.execute(
                select(PoliticoRef)
                .where(PoliticoRef.id_camara.is_not(None))
                .order_by(PoliticoRef.id_camara.asc())
            ).scalars().all()

            if limite_deputados is not None:
                politicos = politicos[:limite_deputados]

            por_id_camara = {
                int(p.id_camara): p
                for p in politicos
                if p.id_camara is not None
            }

            if not por_id_camara:
                return 0, 0, 0

            periodos = [
                (f"{ano}-01-01", f"{ano}-03-31"),
                (f"{ano}-04-01", f"{ano}-06-30"),
                (f"{ano}-07-01", f"{ano}-09-30"),
                (f"{ano}-10-01", f"{ano}-12-31"),
            ]

            for inicio, fim in periodos:
                votacoes = self.client.listar(
                    "votacoes",
                    params={
                        "dataInicio": inicio,
                        "dataFim": fim,
                        "idOrgao": 180,
                    },
                    itens=100,
                )

                for votacao in votacoes:
                    id_votacao = votacao.get("id")
                    if id_votacao is None:
                        continue

                    resposta = self.client.get_opcional(
                        f"votacoes/{id_votacao}/votos"
                    )

                    for registro in resposta.get("dados") or []:
                        if not isinstance(registro, dict):
                            continue

                        deputado = (
                            registro.get("deputado")
                            or registro.get("deputado_")
                            or {}
                        )

                        id_deputado = deputado.get("id")
                        if id_deputado is None:
                            continue

                        politico = por_id_camara.get(int(id_deputado))
                        if politico is None:
                            continue

                        voto_original = (
                            registro.get("tipoVoto")
                            or registro.get("voto")
                            or ""
                        )

                        # Normaliza todos os valores para a restrição do PostgreSQL.
                        chave_voto = str(voto_original).strip().casefold()

                        mapa_votos = {
                            "sim": "sim",
                            "não": "nao",
                            "nao": "nao",
                            "abstenção": "abstencao",
                            "abstencao": "abstencao",
                            "obstrução": "obstrucao",
                            "obstrucao": "obstrucao",
                            "ausente": "ausente",
                            "não informado": "nao_informado",
                            "nao informado": "nao_informado",
                        }

                        tipo_voto = mapa_votos.get(
                            chave_voto,
                            "nao_informado",
                        )

                        # Garantia final: somente valores aceitos pelo banco.
                        valores_permitidos = {
                            "sim",
                            "nao",
                            "abstencao",
                            "obstrucao",
                            "ausente",
                            "nao_informado",
                        }

                        if tipo_voto not in valores_permitidos:
                            tipo_voto = "nao_informado"

                        lidos += 1
                        identificador = f"camara:{id_votacao}"

                        url = (
                            votacao.get("uri")
                            or (
                                "https://dadosabertos.camara.leg.br/"
                                f"api/v2/votacoes/{id_votacao}"
                            )
                        )

                        campos = {
                            "politico_id": politico.id,
                            "identificador_externo": identificador,
                            "casa": "Câmara dos Deputados",
                            "data_votacao": _data(votacao.get("data")),
                            "ementa": (
                                votacao.get("descricao")
                                or votacao.get("descricaoVotacao")
                            ),
                            "voto": tipo_voto,
                            "url_oficial": url,
                            "origem_dados": "oficial",
                            "fonte_nome": "Câmara dos Deputados",
                            "fonte_url": url,
                        }

                        existente = db.session.execute(
                            select(Votacao).where(
                                Votacao.politico_id == politico.id,
                                Votacao.identificador_externo == identificador,
                            )
                        ).scalar_one_or_none()

                        if existente is None:
                            db.session.add(Votacao(**campos))
                            novos += 1
                        else:
                            alterou = False
                            for nome, valor in campos.items():
                                if valor is not None and getattr(
                                    existente, nome
                                ) != valor:
                                    setattr(existente, nome, valor)
                                    alterou = True

                            if alterou:
                                atualizados += 1

                    db.session.commit()

            return lidos, novos, atualizados

        return _executar_log("votacoes", operacao, importar)

    def importar_inicial(
        self,
        ano_inicial,
        ano_final,
        limite_deputados=None,
        limite_proposicoes=None,
    ):
        anos = list(
            range(int(ano_inicial), int(ano_final) + 1)
        )

        resultados = {}

        resultados["partidos"] = self.sincronizar_partidos(
            "carga_inicial"
        )
        resultados["deputados"] = self.sincronizar_deputados(
            "carga_inicial", limite_deputados
        )
        resultados["mandatos"] = self.sincronizar_mandatos(
            "carga_inicial", limite_deputados
        )
        resultados["despesas"] = self.sincronizar_despesas(
            anos, "carga_inicial", limite_deputados
        )
        resultados["proposicoes"] = self.sincronizar_proposicoes(
            anos, "carga_inicial", limite_proposicoes
        )
        resultados["votacoes"] = self.sincronizar_votacoes(
            ano_final, "carga_inicial", limite_deputados
        )

        return resultados

    def atualizar(self, ano, limite_deputados=None):
        resultados = {}

        resultados["partidos"] = self.sincronizar_partidos(
            "atualizacao"
        )
        resultados["deputados"] = self.sincronizar_deputados(
            "atualizacao", limite_deputados
        )
        resultados["mandatos"] = self.sincronizar_mandatos(
            "atualizacao", limite_deputados
        )
        resultados["despesas"] = self.sincronizar_despesas(
            [ano], "atualizacao", limite_deputados
        )
        resultados["proposicoes"] = self.sincronizar_proposicoes(
            [ano], "atualizacao"
        )
        resultados["votacoes"] = self.sincronizar_votacoes(
            ano, "atualizacao", limite_deputados
        )

        return resultados
