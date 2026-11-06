import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { listarPoliticos, obterFiltrosPoliticos } from "../api/politicos";
import SeloDemonstracao from "../components/SeloDemonstracao";
import DadoAusente from "../components/DadoAusente";

const PER_PAGE = 10;
const CHAVES = ["q", "cargo", "partido", "uf"];

function PoliticosPage() {
  const [params, setParams] = useSearchParams();
  const [opcoes, setOpcoes] = useState({ cargos: [], partidos: [], ufs: [] });
  const [resultado, setResultado] = useState({ status: "loading" });

  const page = Math.max(1, Number(params.get("page")) || 1);
  const filtros = Object.fromEntries(CHAVES.map((k) => [k, params.get(k) || ""]));
  const consulta = JSON.stringify([filtros, page]);

  useEffect(() => {
    obterFiltrosPoliticos().then(setOpcoes).catch(() => {});
  }, []);

  useEffect(() => {
    let ativo = true;
    setResultado((anterior) => ({ ...anterior, status: "loading" }));
    listarPoliticos({ ...filtros, page, per_page: PER_PAGE })
      .then((data) => ativo && setResultado({ status: "ready", data }))
      .catch((erro) => ativo && setResultado({ status: "error", mensagem: erro.message }));
    return () => {
      ativo = false;
    };
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
          Busque por nome, cargo, partido e unidade da federação. Registros marcados como
          demonstração são fictícios.
        </p>
      </header>

      <form className="politicos-filtros" onSubmit={(e) => e.preventDefault()} aria-label="Filtros de políticos">
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
            : "Ainda não há políticos cadastrados. Importe o conjunto de demonstração ou uma fonte oficial."}
        </p>
      )}

      {data && (
        <ul className="politicos-lista">
          {data.items.map((p) => (
            <li key={p.id} className="politicos-card">
              <div>
                <h2>
                  <Link to={`/politicos/${p.id}`}>{p.nome_exibicao}</Link>
                  <SeloDemonstracao visivel={p.demonstracao} />
                </h2>
                <p>
                  {p.cargo || <DadoAusente texto="Cargo não informado" />}
                  {" · "}
                  {p.partido || <DadoAusente texto="Partido não informado" />}
                  {" · "}
                  {p.uf || <DadoAusente texto="UF não informada" />}
                </p>
              </div>
              <Link className="button button-secondary" to={`/politicos/${p.id}`}>
                Ver perfil
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
