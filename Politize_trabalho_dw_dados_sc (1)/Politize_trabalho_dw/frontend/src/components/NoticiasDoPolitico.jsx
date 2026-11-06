import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listarNoticiasDoPolitico } from "../api/noticias";
import NoticiaCard from "./NoticiaCard";

function NoticiasDoPolitico({ politicoId, limite = 5 }) {
  const [estado, setEstado] = useState({ status: "loading" });

  useEffect(() => {
    let ativo = true;
    setEstado({ status: "loading" });
    listarNoticiasDoPolitico(politicoId, { per_page: limite })
      .then((data) => ativo && setEstado({ status: "ready", data }))
      .catch((erro) => ativo && setEstado({ status: "error", mensagem: erro.message }));
    return () => {
      ativo = false;
    };
  }, [politicoId, limite]);

  return (
    <section className="noticias-secao" aria-labelledby="noticias-do-politico">
      <h2 id="noticias-do-politico">Notícias relacionadas</h2>
      <p className="noticias-aviso">
        Referências a reportagens de veículos de imprensa, ordenadas da mais recente para a mais
        antiga. A seleção não considera se o tom é positivo ou negativo. Alegações e investigações
        não são fatos comprovados.
      </p>

      {estado.status === "loading" && <p role="status">Carregando notícias…</p>}
      {estado.status === "error" && (
        <p role="alert" className="status-error">
          {estado.mensagem}
        </p>
      )}
      {estado.status === "ready" && estado.data.items.length === 0 && (
        <p>Nenhuma notícia confirmada para este perfil até o momento.</p>
      )}
      {estado.status === "ready" &&
        estado.data.items.map((n) => (
          <NoticiaCard key={n.id} noticia={n} destacarPoliticoId={Number(politicoId)} />
        ))}
      {estado.status === "ready" && estado.data.total > estado.data.items.length && (
        <p>
          <Link className="button button-secondary" to={`/noticias?politico=${politicoId}`}>
            Ver todas as {estado.data.total} notícias
          </Link>
        </p>
      )}
    </section>
  );
}

export default NoticiasDoPolitico;
