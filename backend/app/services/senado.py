from datetime import datetime, timezone

from sqlalchemy import select

from app.adapters.senado import SenadoClient
from app.extensions import db
from app.models.cargo_eletivo import CargoEletivo
from app.models.politico import Politico

FONTE = "senado_federal"
FONTE_NOME = "Senado Federal"
FONTE_URL = "https://legis.senado.leg.br/dadosabertos/senador/lista/atual"


def sincronizar_senadores(client=None):
    client = client or SenadoClient()
    registros = client.listar_em_exercicio()
    novos = atualizados = 0

    for item in registros:
        codigo = item["id_senado"]
        politico = db.session.scalar(select(Politico).where(Politico.id_senado == codigo))
        if politico is None:
            politico = db.session.scalar(select(Politico).where(
                Politico.nome_completo.ilike(item["nome_completo"], escape="\\")
            ))

        agora = datetime.now(timezone.utc)
        campos = {
            "nome_completo": item["nome_completo"],
            "nome_urna": item["nome_urna"],
            "cargo": "Senador",
            "uf": item["uf"],
            "partido": item["partido"],
            "id_senado": codigo,
            "dados_camara": politico.dados_camara if politico and politico.dados_camara else None,
            "origem_dados": "oficial",
            "fonte_nome": FONTE_NOME,
            "fonte_url": item["perfil_url"] or FONTE_URL,
            "atualizado_em": agora,
        }

        if politico is None:
            politico = Politico(slug=f"senador-{codigo}", coletado_em=agora, **campos)
            db.session.add(politico)
            db.session.flush()
            novos += 1
        else:
            alterou = False
            for nome, valor in campos.items():
                if valor is not None and getattr(politico, nome) != valor:
                    setattr(politico, nome, valor)
                    alterou = True
            politico.atualizado_em = agora
            atualizados += int(alterou)

        cargo = db.session.scalar(select(CargoEletivo).where(
            CargoEletivo.origem == FONTE,
            CargoEletivo.identificador_externo == str(codigo),
        ))
        dados_cargo = {
            "politico_id": politico.id,
            "cargo": "Senador",
            "esfera": "federal",
            "uf": item["uf"],
            "municipio": None,
            "partido": item["partido"],
            "ano_inicio": None,
            "ano_fim": None,
            "situacao": "em_exercicio",
            "identificador_externo": str(codigo),
            "origem": FONTE,
            "fonte_nome": FONTE_NOME,
            "fonte_url": item["perfil_url"] or FONTE_URL,
            "dados_origem": item,
        }
        if cargo is None:
            db.session.add(CargoEletivo(**dados_cargo))
        else:
            for nome, valor in dados_cargo.items():
                if valor is not None:
                    setattr(cargo, nome, valor)
            cargo.atualizado_em = agora

    db.session.commit()
    return {"lidos": len(registros), "novos": novos, "atualizados": atualizados}
