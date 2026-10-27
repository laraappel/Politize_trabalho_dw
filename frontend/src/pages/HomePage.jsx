import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getHealth } from "../api/client";
import {
  IconBalance,
  IconChecklist,
  IconNews,
  IconSearch,
  IconUsers,
} from "../components/icons";

function HomePage() {
  const [health, setHealth] = useState({ state: "loading" });

  useEffect(() => {
    getHealth()
      .then((data) => setHealth({ state: "ready", data }))
      .catch(() => setHealth({ state: "error" }));
  }, []);

  return (
    <section className="page home">
      <header className="hero">
        <p className="eyebrow">Plataforma cívica apartidária</p>
        <h1>Acompanhe a vida pública com informação clara e verificável.</h1>
        <p className="lede">
          O Voto Transparente reúne dados sobre políticos, cargos, mandatos, despesas
          públicas, propostas e notícias para apoiar o voto informado.
        </p>
        <div className="hero-actions">
          <Link className="button button-primary" to="/politicos">
            <IconSearch className="icon" />
            Pesquisar políticos
          </Link>
          <Link className="button button-secondary" to="/transparencia">
            Abrir portal da transparência
          </Link>
        </div>
      </header>

      <ul className="feature-grid">
        <li>
          <IconUsers className="icon" />
          <h2>Políticos</h2>
          <p>Consulte perfis, cargos e trajetória pública.</p>
        </li>
        <li>
          <IconBalance className="icon" />
          <h2>Transparência</h2>
          <p>Acompanhe remunerações, despesas e patrimônio declarado.</p>
        </li>
        <li>
          <IconNews className="icon" />
          <h2>Notícias</h2>
          <p>Leia cobertura política com indicação de fontes.</p>
        </li>
        <li>
          <IconChecklist className="icon" />
          <h2>Colinha</h2>
          <p>Organize, de forma privada, suas anotações de voto.</p>
        </li>
      </ul>

      <aside className="status-card" aria-live="polite">
        <h2>Status da API</h2>
        {health.state === "loading" && <p>Verificando conexão com o backend...</p>}
        {health.state === "error" && (
          <p className="status-error">Não foi possível conectar à API.</p>
        )}
        {health.state === "ready" && (
          <dl className="status-list">
            <div>
              <dt>API</dt>
              <dd>{health.data.api.status}</dd>
            </div>
            <div>
              <dt>Banco de dados</dt>
              <dd>{health.data.database.status}</dd>
            </div>
          </dl>
        )}
      </aside>
    </section>
  );
}

export default HomePage;
