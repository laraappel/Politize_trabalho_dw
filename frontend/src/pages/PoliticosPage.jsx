import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { listarDeputadosCamara, listarPartidosCamara } from "../api/camara";
import { listarCargosEletivos, obterFiltrosCargosEletivos } from "../api/cargos";
import PoliticoAvatar from "../components/PoliticoAvatar";

const PER_PAGE = 10;
const CHAVES = ["q", "cargo", "partido", "uf", "ano"];

function PoliticosPage() {
  const [params, setParams] = useSearchParams();
  const [opcoes, setOpcoes] = useState({ cargos: [], partidos: [], ufs: [], anos: [] });
  const [erroFiltros, setErroFiltros] = useState("");
  const [resultado, setResultado] = useState({ status: "loading" });

  const page = Math.max(1, Number(params.get("page")) || 1);
  const filtros = Object.fromEntries(CHAVES.map((k) => [k, params.get(k) || ""]));
  const consulta = JSON.stringify([filtros, page]);

  useEffect(() => {
    Promise.all([
      listarPartidosCamara(),
      listarDeputadosCamara({ pagina: 1, limite: 100 }),
      obterFiltrosCargosEletivos(),
    ])
      .then(([partidos, deputados, cargos]) => setOpcoes({
        cargos: ["Deputado federal", ...(cargos.cargos || [])].filter((cargo, indice, lista) => lista.indexOf(cargo) === indice),
        anos: cargos.anos || [],
        partidos: [...new Set([
          ...(partidos.dados || []).map((partido) => partido.sigla),
          ...(cargos.partidos || []),
        ].filter(Boolean))].sort(),
        ufs: [...new Set([
          ...(deputados.dados || []).map((deputado) => deputado.uf),
          ...(cargos.ufs || []),
        ].filter(Boolean))].sort(),
      }))
      .catch((erro) => setErroFiltros(erro.message));
  }, []);

  useEffect(() => {
    let ativo = true;
    setResultado((anterior) => ({ ...anterior, status: "loading" }));

    if ((filtros.cargo && filtros.cargo.toLowerCase() !== "deputado federal") || filtros.ano) {
      listarCargosEletivos({ q: filtros.q, partido: filtros.partido, uf: filtros.uf, cargo: filtros.cargo, ano: filtros.ano, page, per_page: PER_PAGE })
        .then((response) => {
          if (!ativo) return;
          setResultado({
            status: "ready",
            data: {
              items: (response.items || []).map((item) => ({
                id: item.politico_id,
                nome_exibicao: item.nome,
                cargo: item.cargo,
                partido: item.partido,
                uf: item.uf,
                demonstracao: false,
                atualizado_em: item.atualizado_em,
                ano_eleicao: item.ano_eleicao,
                situacao_eleitoral: item.situacao,
              })),
              total: response.total || 0,
              page: response.page || page,
              per_page: response.per_page || PER_PAGE,
              pages: response.pages || 0,
            },
          });
        })
        .catch((erro) => ativo && setResultado({ status: "error", mensagem: erro.message }));
    } else {
      listarDeputadosCamara({ q: filtros.q, partido: filtros.partido, uf: filtros.uf, pagina: page, limite: PER_PAGE })
        .then((response) => {
          if (!ativo) return;
          const paginacao = response.paginacao || {};
          setResultado({
            status: "ready",
            data: {
              items: (response.dados || []).map((p) => ({
                id: p.id,
                nome_exibicao: p.nome,
                cargo: p.cargo,
                partido: p.partido,
                uf: p.uf,
                demonstracao: false,
                atualizado_em: p.atualizado_em,
                id_camara: p.id_camara,
              })),
              total: paginacao.total || 0,
              page: paginacao.pagina || page,
              per_page: paginacao.limite || PER_PAGE,
              pages: paginacao.limite ? Math.ceil((paginacao.total || 0) / paginacao.limite) : 0,
            },
          });
        })
        .catch((erro) => ativo && setResultado({ status: "error", mensagem: erro.message }));
    }

    return () => { ativo = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [consulta]);

  function atualizar(mudancas, voltarParaPrimeira = true) {
    const proximo = new URLSearchParams(params);
    Object.entries(mudancas).forEach(([k, v]) => (v ? proximo.set(k, v) : proximo.delete(k)));
    if (voltarParaPrimeira) proximo.delete("page");
    setParams(proximo);
  }

  const aoMudar = (campo) => (e) => atualizar({ [campo]: e.target.value });
  const temFiltro = CHAVES.some((k) => params.get(k));
  const data = resultado.data;

  return (
    <section className="page politicos-pagina">
      <header className="page-header">
        <p className="eyebrow">Políticos</p>
        <h1>Pesquisa de políticos</h1>
        <p className="lede">
          Consulte cargos eletivos com dados oficiais disponíveis: deputados federais pela Câmara
          dos Deputados, senadores pelo Senado Federal e resultados eleitorais do TSE para cargos federais,
          estaduais e municipais.
        </p>
      </header>

      {erroFiltros && <p role="alert" className="status-error">Não foi possível carregar as opções de filtro: {erroFiltros}</p>}
      <form className="politicos-filtros" onSubmit={(e) => e.preventDefault()} role="search" aria-label="Filtros de políticos">
        <label>
          Nome
          <input
            type="search"
            value={filtros.q}
            maxLength={80}
            placeholder="Nome ou nome de urna"
            onChange={aoMudar("q")}
          />
        </label>
        <label>
          Cargo
          <select value={filtros.cargo} onChange={aoMudar("cargo")}>
            <option value="">Todos</option>
            {opcoes.cargos.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </label>
        <label>
          Partido
          <select value={filtros.partido} onChange={aoMudar("partido")}>
            <option value="">Todos</option>
            {opcoes.partidos.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </label>
        <label>
          UF
          <select value={filtros.uf} onChange={aoMudar("uf")}>
            <option value="">Todas</option>
            {opcoes.ufs.map((uf) => (
              <option key={uf} value={uf}>{uf}</option>
            ))}
          </select>
        </label>
        <label>
          Ano da eleição
          <select value={filtros.ano} onChange={aoMudar("ano")}>
            <option value="">Todos</option>
            {opcoes.anos.map((ano) => (
              <option key={ano} value={ano}>{ano}</option>
            ))}
          </select>
        </label>
        {temFiltro && (
          <button type="button" className="button button-secondary" onClick={() => setParams({})}>
            Limpar filtros
          </button>
        )}
      </form>

      <div aria-live="polite">
        {resultado.status === "error" && <p role="alert" className="status-error">{resultado.mensagem}</p>}
        {resultado.status === "loading" && !data && <p role="status">Carregando políticos…</p>}
        {data && (
          <p className="politicos-contagem">
            {data.total} {data.total === 1 ? "registro encontrado" : "registros encontrados"}
            {resultado.status === "loading" && " (atualizando…)"}
          </p>
        )}
      </div>

      {data && data.items.length === 0 && resultado.status !== "error" && (
        <p className="notice">
          {temFiltro
            ? "Nenhum político corresponde aos filtros escolhidos."
            : "Ainda não há políticos cadastrados."}
        </p>
      )}

      {data && (
        <ul className="politicos-lista">
          {data.items.map((p) => (
            <li key={p.id} className="politicos-card">
              <PoliticoAvatar politico={p} />
              <div className="politicos-card-content">
                <h2>
                  <Link to={`/politicos/${p.id}`}>{p.nome_exibicao}</Link>
                </h2>
                <p className="politicos-card-meta">
                  {[p.cargo, p.partido, p.uf].filter(Boolean).join(" · ") || "Dados de cargo indisponíveis"}
                </p>
                {p.ano_eleicao && (
                  <p className="politicos-card-election">Eleição {p.ano_eleicao}{p.situacao_eleitoral ? ` · ${p.situacao_eleitoral}` : ""}</p>
                )}
              </div>
              <Link className="button button-secondary politicos-card-link" to={`/politicos/${p.id}`} aria-label={`Ver perfil de ${p.nome_exibicao}`}>
                Ver perfil <span aria-hidden="true">→</span>
              </Link>
            </li>
          ))}
        </ul>
      )}

      {data && data.pages > 1 && (
        <nav className="noticias-paginacao" aria-label="Paginação">
          <button type="button" className="button button-secondary" disabled={page <= 1}
            onClick={() => atualizar({ page: String(page - 1) }, false)}>
            Anterior
          </button>
          <span>Página {data.page} de {data.pages}</span>
          <button type="button" className="button button-secondary" disabled={page >= data.pages}
            onClick={() => atualizar({ page: String(page + 1) }, false)}>
            Próxima
          </button>
        </nav>
      )}
    </section>
  );
}

export default PoliticosPage;
