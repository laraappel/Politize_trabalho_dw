import { useState } from "react";
import { Link } from "react-router-dom";
import { obterNoticia } from "../api/noticias";

const GRAUS = { alta: "alta", media: "média", baixa: "baixa", manual: "revisão manual" };
const TIPOS_ATUALIZACAO = {
  desdobramento: "Desdobramento",
  correcao: "Correção",
  complemento: "Complemento",
  alteracao_titulo: "Título alterado pelo veículo",
};

const NATUREZA_PADRAO = {
  codigo: "nao_classificado",
  rotulo: "Sem classificação",
  aviso: "A natureza desta notícia ainda não foi classificada.",
  origem: "heuristica",
};

function formatarData(iso) {
  if (!iso) return "Data não informada";
  return new Date(iso).toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "long",
    year: "numeric",
    timeZone: "America/Sao_Paulo",
  });
}

function Atualizacoes({ noticiaId, total }) {
  const [estado, setEstado] = useState({ status: "idle", itens: [] });

  function aoAlternar(evento) {
    if (!evento.target.open || estado.status !== "idle") return;
    setEstado({ status: "loading", itens: [] });
    obterNoticia(noticiaId)
      .then((d) => setEstado({ status: "ready", itens: d?.atualizacoes || [] }))
      .catch(() => setEstado({ status: "error", itens: [] }));
  }

  return (
    <details className="noticias-atualizacoes" onToggle={aoAlternar}>
      <summary>Desdobramentos e correções ({total})</summary>
      {estado.status === "loading" && <p>Carregando…</p>}
      {estado.status === "error" && (
        <p role="alert">Não foi possível carregar as atualizações.</p>
      )}
      {estado.status === "ready" && (
        <ul>
          {estado.itens.map((a) => (
            <li key={a.id}>
              <strong>{TIPOS_ATUALIZACAO[a.tipo] || a.tipo}</strong> ·{" "}
              <time dateTime={a.criado_em}>{formatarData(a.criado_em)}</time>
              <p>{a.descricao}</p>
              {a.url_referencia && (
                <a href={a.url_referencia} target="_blank" rel="noopener noreferrer">
                  Ver referência
                </a>
              )}
            </li>
          ))}
        </ul>
      )}
    </details>
  );
}

function NoticiaCard({ noticia, destacarPoliticoId }) {
  if (!noticia) return null;

  const natureza = noticia.natureza || NATUREZA_PADRAO;
  const veiculo = noticia.veiculo || { nome: "Fonte não informada" };
  const politicos = Array.isArray(noticia.politicos) ? noticia.politicos : [];
  const mostrarAviso = natureza.codigo !== "nao_classificado";

  return (
    <article className="noticias-card">
      <p className="noticias-meta">
        <span className="noticias-veiculo">{veiculo.nome}</span>
        <span aria-hidden="true"> · </span>
        <time dateTime={noticia.publicado_em || undefined}>
          {formatarData(noticia.publicado_em)}
        </time>
      </p>

      <h2 className="noticias-titulo">
        <a href={noticia.url_original || "#"} target="_blank" rel="noopener noreferrer">
          {noticia.titulo_original || noticia.titulo || "Sem título"}
          <span className="noticias-sr">
            {" "}
            (abre a matéria original em {veiculo.nome}, nova aba)
          </span>
        </a>
      </h2>

      {noticia.resumo && <p className="noticias-resumo">{noticia.resumo}</p>}

      <div className="noticias-tags">
        {noticia.assunto && (
          <span className="noticias-tag">{noticia.assunto.nome}</span>
        )}
        <span
          className={`noticias-tag noticias-natureza noticias-natureza-${natureza.codigo}`}
        >
          {natureza.rotulo}
        </span>
      </div>

      {mostrarAviso && (
        <p className="noticias-aviso">
          {natureza.aviso}
          {natureza.origem === "heuristica" &&
            " Classificação automática, sujeita a revisão."}
        </p>
      )}

      {politicos.length > 0 && (
        <p className="noticias-politicos">
          Relacionada a:{" "}
          {politicos.map((p, i) => (
            <span key={p.id}>
              {i > 0 && ", "}
              {p.id === destacarPoliticoId ? (
                <strong>{p.nome}</strong>
              ) : (
                <Link to={`/politicos/${p.id}`}>{p.nome}</Link>
              )}{" "}
              <small title="Grau de confirmação do vínculo entre a matéria e o político">
                (vínculo {GRAUS[p.grau_confirmacao] || p.grau_confirmacao})
              </small>
            </span>
          ))}
        </p>
      )}

      {noticia.total_atualizacoes > 0 && (
        <Atualizacoes
          noticiaId={noticia.id}
          total={noticia.total_atualizacoes}
        />
      )}
    </article>
  );
}

export default NoticiaCard;