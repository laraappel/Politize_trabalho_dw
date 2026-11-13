import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { listarNoticias, listarVeiculos, obterFiltrosNoticias } from "../api/noticias";
import NoticiaCard from "../components/NoticiaCard";

const PER_PAGE = 10;
const CHAVES = ["q", "politico", "veiculo", "assunto", "natureza", "de", "ate", "ordem"];

function NoticiasPage() {
  const [params, setParams] = useSearchParams();
  const [opcoes, setOpcoes] = useState({ politicos: [], veiculos: [], assuntos: [], naturezas: [] });
  const [erroFiltros, setErroFiltros] = useState("");
  const [fontes, setFontes] = useState([]);
  const [erroFontes, setErroFontes] = useState("");
  const [resultado, setResultado] = useState({ status: "loading" });

  const page = Math.max(1, Number(params.get("page")) || 1);
  const filtros = Object.fromEntries(CHAVES.map((k) => [k, params.get(k) || ""]));
  const consulta = JSON.stringify([filtros, page]);

  useEffect(() => {
    obterFiltrosNoticias()
      .then(setOpcoes)
      .catch((erro) => setErroFiltros(erro.message));
    listarVeiculos()
      .then((d) => setFontes(d.items))
      .catch((erro) => setErroFontes(erro.message));
  }, []);

  useEffect(() => {
    let ativo = true;
    setResultado((anterior) => ({ ...anterior, status: "loading" }));
    listarNoticias({ ...filtros, page, per_page: PER_PAGE })
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
    <section className="page noticias-pagina">
      <header className="page-header">
        <p className="eyebrow">Notícias</p>
        <h1>Notícias políticas</h1>
        <p className="lede">
          Referências a reportagens sobre políticos brasileiros, com link para a matéria original.
          Este site não reproduz o texto das reportagens.
        </p>
      </header>

      <div className="notice" role="note">
        <strong>Como ler:</strong> a seleção considera a relação da notícia com o político, não se o
        conteúdo é favorável ou desfavorável. Alegações, opiniões e investigações são identificadas e
        não devem ser lidas como fatos comprovados. A classificação automática pode conter erros.
      </div>

      <form className="noticias-filtros" onSubmit={(e) => e.preventDefault()} aria-label="Filtros de notícias">
        <label className="noticias-filtro-busca">
          Buscar notícia
          <input
            type="search"
            value={filtros.q}
            onChange={aoMudar("q")}
            placeholder="Digite título, assunto ou fonte..."
          />
        </label>
        <label>
          Político
          <select value={filtros.politico} onChange={aoMudar("politico")} disabled={opcoes.politicos.length === 0}>
            <option value="">{opcoes.politicos.length ? "Todos" : "Sem vínculos cadastrados"}</option>
            {opcoes.politicos.map((p) => (
              <option key={p.id} value={p.id}>{p.nome}</option>
            ))}
          </select>
        </label>
        <label>
          Veículo
          <select value={filtros.veiculo} onChange={aoMudar("veiculo")}>
            <option value="">Todos</option>
            {opcoes.veiculos.map((v) => (
              <option key={v.slug} value={v.slug}>{v.nome}</option>
            ))}
          </select>
        </label>
        <label>
          Assunto
          <select value={filtros.assunto} onChange={aoMudar("assunto")}>
            <option value="">Todos</option>
            {opcoes.assuntos.map((a) => (
              <option key={a.slug} value={a.slug}>{a.nome}</option>
            ))}
          </select>
        </label>
        <label>
          Natureza
          <select value={filtros.natureza} onChange={aoMudar("natureza")}>
            <option value="">Todas</option>
            {opcoes.naturezas.map((n) => (
              <option key={n.codigo} value={n.codigo}>{n.rotulo}</option>
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
        <label>
          Ordem
          <select value={filtros.ordem || "recentes"} onChange={aoMudar("ordem")}>
            <option value="recentes">Mais recentes primeiro</option>
            <option value="antigas">Mais antigas primeiro</option>
          </select>
        </label>
        {temFiltro && (
          <button type="button" className="button button-secondary" onClick={() => setParams({})}>
            Limpar filtros
          </button>
        )}
      </form>
      {!erroFiltros && opcoes.politicos.length === 0 && (
        <p className="noticias-filtro-aviso">O filtro por político ficará disponível quando as notícias tiverem vínculos revisados com políticos cadastrados.</p>
      )}
      {erroFiltros && <p role="alert" className="status-error">Não foi possível carregar as opções de filtro: {erroFiltros}</p>}
      {erroFontes && <p role="alert" className="status-error">Não foi possível carregar as fontes: {erroFontes}</p>}

      <div aria-live="polite">
        {resultado.status === "error" && (
          <p role="alert" className="status-error">{resultado.mensagem}</p>
        )}
        {resultado.status === "loading" && !data && <p role="status">Carregando notícias…</p>}
        {data && (
          <p className="noticias-contagem">
            {data.total} {data.total === 1 ? "notícia encontrada" : "notícias encontradas"}
            {resultado.status === "loading" && " (atualizando…)"}
          </p>
        )}
      </div>

      {data && data.items.length === 0 && resultado.status !== "error" && (
        <p className="notice">
          {temFiltro
            ? "Nenhuma notícia corresponde aos filtros escolhidos."
            : "Ainda não há notícias confirmadas. Elas aparecem aqui depois que a coleta das fontes autorizadas associa matérias a políticos cadastrados."}
        </p>
      )}

      {data && data.items.map((n) => <NoticiaCard key={n.id} noticia={n} />)}

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

      {fontes.length > 0 && (
        <details className="noticias-fontes">
          <summary>Fontes monitoradas e base de autorização</summary>
          <ul>
            {fontes.map((f) => (
              <li key={f.slug}>
                <strong>{f.nome}</strong> — {f.coleta_autorizada ? "coleta ativa" : "coleta desativada"}.{" "}
                {f.base_autorizacao}{" "}
                {f.url_termos && (
                  <a href={f.url_termos} target="_blank" rel="noopener noreferrer">Termos</a>
                )}
              </li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}

export default NoticiasPage;
