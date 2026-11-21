"""Associação notícia -> político baseada em evidências verificáveis.

Princípios:
1. Coincidência de nome NÃO basta. Só é confirmada automaticamente a associação
   com (a) identificador oficial presente nos links da matéria, ou (b) nome
   completo (2+ palavras) acompanhado de título político (deputado, senador...)
   próximo ao nome, sem homonímia no cadastro.
2. Nome completo sem contexto, homônimos e apelidos ficam `pendente_revisao`
   (não aparecem publicamente até revisão humana).
3. Apelido de uma palavra sem contexto de cargo é ignorado.
4. Cada decisão registra método, grau e as evidências (trechos) usadas.

Só título e resumo são analisados: o corpo da matéria não é coletado.
"""
import re
from dataclasses import dataclass, field

from app.services.noticias.normalizacao import normalizar_texto, remover_acentos

TITULOS_POLITICOS = {
    "deputado", "deputada", "deputados", "deputadas",
    "senador", "senadora", "senadores", "senadoras",
    "governador", "governadora", "prefeito", "prefeita",
    "vereador", "vereadora", "ministro", "ministra",
}
JANELA_ANTES = 6
JANELA_DEPOIS = 6

_RE_ID_CAMARA = re.compile(r"camara\.leg\.br/deputados/(\d+)")
# Padrão de URL de perfil do Senado: validar contra o site antes de depender dele.
_RE_ID_SENADO = re.compile(r"senado\.leg\.br/web/senadores/senador/-/perfil/(\d+)")
_RE_PALAVRA = re.compile(r"\w+", re.UNICODE)


@dataclass(frozen=True)
class PoliticoCadastro:
    id: int
    nome_completo: str
    nome_urna: str | None = None
    apelidos: tuple[str, ...] = ()
    cargo: str | None = None
    partido: str | None = None
    id_camara: int | None = None
    id_senado: int | None = None


@dataclass
class Associacao:
    politico_id: int
    status: str  # confirmada | pendente_revisao
    grau: str  # alta | media | baixa
    metodo: str
    evidencias: list[dict] = field(default_factory=list)


@dataclass
class _Ocorrencia:
    politico_id: int
    tipo: str  # nome_completo | apelido
    ini: int
    fim: int  # índice de token (exclusivo)
    campo: str
    trecho: str
    titulo_proximo: str | None
    ambiguo: bool = False


def _tokens(texto: str):
    return [
        (normalizar_texto(m.group()), m.start(), m.end()) for m in _RE_PALAVRA.finditer(texto)
    ]


def _nomes_de(p: PoliticoCadastro):
    """(tuple de tokens normalizados, tipo) para cada forma de nome utilizável."""
    saida = []
    for nome in (p.nome_completo, p.nome_urna):
        if nome:
            toks = tuple(normalizar_texto(nome).split())
            if len(toks) >= 2:
                saida.append((toks, "nome_completo"))
    for apelido in p.apelidos:
        toks = tuple(normalizar_texto(apelido).split())
        if toks:
            saida.append((toks, "apelido"))
    return saida


class AssociadorPoliticos:
    def __init__(self, politicos: list[PoliticoCadastro]):
        self._politicos = {p.id: p for p in politicos}
        self._indice: dict[tuple, list[tuple[int, str]]] = {}
        for p in politicos:
            for toks, tipo in _nomes_de(p):
                self._indice.setdefault(toks, []).append((p.id, tipo))
        self._por_camara = {p.id_camara: p.id for p in politicos if p.id_camara}
        self._por_senado = {p.id_senado: p.id for p in politicos if p.id_senado}
        self._tamanhos = sorted({len(k) for k in self._indice}, reverse=True)

    # -- API pública --------------------------------------------------------
    def associar(self, titulo: str, resumo: str | None, links_html: str = "") -> list[Associacao]:
        resultado: dict[int, Associacao] = {}

        for pid, evid in self._por_identificador(links_html).items():
            resultado[pid] = Associacao(pid, "confirmada", "alta", "identificador_oficial", [evid])

        ocorrencias = self._ocorrencias("titulo", titulo) + self._ocorrencias("resumo", resumo or "")
        por_politico: dict[int, list[_Ocorrencia]] = {}
        for oc in ocorrencias:
            por_politico.setdefault(oc.politico_id, []).append(oc)

        for pid, ocs in por_politico.items():
            if pid in resultado:
                continue
            decisao = self._decidir(pid, ocs)
            if decisao:
                resultado[pid] = decisao
        return list(resultado.values())

    # -- internos -----------------------------------------------------------
    def _por_identificador(self, links_html: str) -> dict[int, dict]:
        achados = {}
        for m in _RE_ID_CAMARA.finditer(links_html):
            pid = self._por_camara.get(int(m.group(1)))
            if pid:
                achados[pid] = {"tipo": "identificador_oficial", "campo": "links", "trecho": m.group(0)}
        for m in _RE_ID_SENADO.finditer(links_html):
            pid = self._por_senado.get(int(m.group(1)))
            if pid:
                achados[pid] = {"tipo": "identificador_oficial", "campo": "links", "trecho": m.group(0)}
        return achados

    def _ocorrencias(self, campo: str, texto: str) -> list[_Ocorrencia]:
        if not texto or not self._indice:
            return []
        toks = _tokens(texto)
        normais = [t[0] for t in toks]
        brutas: list[tuple[int, int, tuple, list]] = []
        for tam in self._tamanhos:
            for i in range(len(normais) - tam + 1):
                chave = tuple(normais[i : i + tam])
                if chave in self._indice:
                    brutas.append((i, i + tam, chave, self._indice[chave]))
        # descarta ocorrências contidas em outra mais longa (ex.: nome curto dentro de nome longo)
        brutas = [
            b for b in brutas
            if not any(o is not b and o[0] <= b[0] and b[1] <= o[1] and (o[1] - o[0]) > (b[1] - b[0]) for o in brutas)
        ]
        saida = []
        for ini, fim, chave, donos in brutas:
            ambiguo = len({pid for pid, _ in donos}) > 1
            janela = normais[max(0, ini - JANELA_ANTES) : ini] + normais[fim : fim + JANELA_DEPOIS]
            titulo_prox = next((t for t in janela if t in TITULOS_POLITICOS), None)
            trecho = texto[
                toks[max(0, ini - JANELA_ANTES)][1] : toks[min(len(toks), fim + JANELA_DEPOIS) - 1][2]
            ]
            for pid, tipo in donos:
                saida.append(_Ocorrencia(pid, tipo, ini, fim, campo, trecho, titulo_prox, ambiguo))
        return saida

    def _decidir(self, pid: int, ocs: list[_Ocorrencia]) -> Associacao | None:
        evidencias = [
            {"tipo": o.tipo, "campo": o.campo, "trecho": o.trecho, "titulo_proximo": o.titulo_proximo}
            for o in ocs
        ]
        completos = [o for o in ocs if o.tipo == "nome_completo"]
        ambiguo = any(o.ambiguo for o in ocs)

        if completos:
            if ambiguo:
                evidencias.append({"tipo": "homonimia", "detalhe": "nome compartilhado por mais de um cadastro"})
                return Associacao(pid, "pendente_revisao", "baixa", "homonimia", evidencias)
            if any(o.titulo_proximo for o in completos):
                return Associacao(pid, "confirmada", "alta", "nome_completo_e_cargo", evidencias)
            return Associacao(pid, "pendente_revisao", "media", "nome_completo", evidencias)

        # só apelido: exige título político próximo e, mesmo assim, vai para revisão
        if any(o.titulo_proximo for o in ocs):
            return Associacao(pid, "pendente_revisao", "baixa" if ambiguo else "media", "apelido_e_cargo", evidencias)
        return None
