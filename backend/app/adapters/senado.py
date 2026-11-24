import requests
import xml.etree.ElementTree as ET


class SenadoAPIError(Exception):
    pass


class SenadoClient:
    BASE_URL = "https://legis.senado.leg.br/dadosabertos/senador/lista/atual"

    def __init__(self, timeout=40, session=None):
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update({
            "Accept": "application/xml, text/xml, */*",
            "User-Agent": "VotoTransparente/1.0 (dados abertos; projeto academico)",
        })

    def listar_em_exercicio(self):
        resposta = self.session.get(self.BASE_URL, timeout=self.timeout)
        resposta.raise_for_status()

        try:
            raiz = ET.fromstring(resposta.content)
        except ET.ParseError as exc:
            raise SenadoAPIError("Resposta XML inválida da API do Senado.") from exc

        resultado = []
        for elemento in raiz.iter():
            if elemento.tag.rsplit("}", 1)[-1] != "Parlamentar":
                continue

            def texto(nome):
                filho = next((e for e in elemento.iter() if e.tag.rsplit("}", 1)[-1] == nome), None)
                return (filho.text or "").strip() if filho is not None else None

            codigo = texto("CodigoParlamentar")
            if not codigo:
                continue

            partido = next((
                texto(nome)
                for nome in ("SiglaPartidoParlamentar", "SiglaPartido")
                if texto(nome)
            ), None)

            resultado.append({
                "id_senado": int(codigo),
                "nome_completo": texto("NomeCompletoParlamentar") or texto("NomeParlamentar"),
                "nome_urna": texto("NomeParlamentar"),
                "sexo": texto("SexoParlamentar"),
                "uf": texto("UfParlamentar"),
                "partido": partido,
                "foto_url": texto("UrlFotoParlamentar"),
                "perfil_url": texto("UrlPaginaParlamentar"),
                "email": texto("EmailParlamentar"),
            })
        return resultado
