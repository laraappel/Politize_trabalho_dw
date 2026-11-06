import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { listarDespesas, obterFiltrosTransparencia, obterPanorama } from "../api/transparencia";
import DadoAusente from "../components/DadoAusente";
import SeloDemonstracao from "../components/SeloDemonstracao";
import { formatarData, formatarDinheiro } from "../formatters";

const PER_PAGE = 10;
const CHAVES = ["categoria", "uf", "de", "ate"];

function TransparenciaPage() {
  const [params, setParams] = useSearchParams();
  const [panorama, setPanorama] = useState(null);
  const [opcoes, setOpcoes] = useState({ categorias: [], ufs: [] });
  const [resultado, setResultado] = useState({ status: "loading" });
  const page = Math.max(1, Number(params.get("page")) || 1);
  const filtros = Object.fromEntries(CHAVES.map((k) => [k, params.get(k) || ""]));
  const consulta = JSON.stringify([filtros, page]);

  useEffect(() => {
    obterPanorama().then(setPanorama).catch(() => {});
    obterFiltrosTransparencia().then(setOpcoes).catch(() => {});
  }, []);

  useEffect(() => {
    let ativo = true;
    setResultado((anterior) => ({ ...anterior, status: "loading" }));
    listarDespesas({ ...filtros, page, per_page: PER_PAGE })
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
  const data = resultado.data;
  const resumo = data?.resumo_financeiro;

  return (
    <section className="page transparencia-pagina">
      <header className="page-header">
        <p className="eyebrow">Transparência</p>
        <h1>Portal da transparência</h1>
        <p className="lede">
          Despesas com categoria e período. Valores ausentes aparecem como não informados, nunca como zero.
        </p>
      </header>

      {panorama && (
        <ul className="feature-grid">
          <li>
            <h2>{panorama.politicos}</h2>
            <p>políticos no cadastro ({panorama.politicos_demonstracao} de demonstração)</p>
          </li>
          <li>
            <h2>{panorama.projetos}</h2>
            <p>projetos vinculados</p>
          </li>
          <li>
            <h2>{panorama.votacoes}</h2>
            <p>votações registradas</p>
          </li>
          <li>
            <h2>{panorama.despesas.registros}</h2>
            <p>registros de despesa ({panorama.despesas.registros_sem_valor} sem valor)</p>
          </li>
        </ul>
      )}

      <form className="politicos-filtros" onSubmit={(e) => e.preventDefault()} aria-label="Filtros de despesas">
        <label>
          Categoria
          <select value={filtros.categoria} onChange={aoMudar("categoria")}>
            <option value="">Todas</option>
            {opcoes.categorias.map((c) => (
              <option key={c} value={c}>{c}</option>
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
          De
          <input type="date" value={filtros.de} max={filtros.ate || undefined} onChange={aoMudar("de")} />
        </label>
        <label>
          Até
          <input type="date" value={filtros.ate} min={filtros.de || undefined} onChange={aoMudar("ate")} />
        </label>
      </form>

      {resumo && resumo.registros > 0 && (
        <p className="notice">
          {resumo.completo
            ? `Soma dos valores informados neste filtro: ${formatarDinheiro(resumo.soma_valores_informados)}.`
            : `Filtro incompleto: ${resumo.registros_sem_valor} registro(s) sem valor. Soma apenas do informado: ${formatarDinheiro(resumo.soma_valores_informados) || "indisponível"}.`}
        </p>
      )}

      {resultado.status === "error" && <p role="alert" className="status-error">{resultado.mensagem}</p>}
      {resultado.status === "loading" && !data && <p role="status">Carregando despesas…</p>}
      {data && data.items.length === 0 && (
        <p className="notice">Nenhuma despesa corresponde aos filtros. A ausência de registros não representa gasto zero.</p>
      )}

      {data && (
        <ul className="lista-simples">
          {data.items.map((d) => (
            <li key={d.id} className="politicos-card">
              <div>
                <h2>
                  {d.politico ? (
                    <Link to={`/politicos/${d.politico.id}`}>{d.politico.nome_exibicao}</Link>
                  ) : (
                    "Político não informado"
                  )}
                  <SeloDemonstracao visivel={d.demonstracao} />
                </h2>
                <p>
                  {d.categoria} · {formatarData(d.periodo.inicio)} — {formatarData(d.periodo.fim)} ·{" "}
                  {formatarDinheiro(d.valor) || <DadoAusente texto="valor não informado" />}
                </p>
                <p>{d.descricao}</p>
              </div>
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

export default TransparenciaPage;
