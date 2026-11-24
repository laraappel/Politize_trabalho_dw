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
      <div className="home-hero-grid">
        <header className="hero home-hero">
          <div className="home-hero-copy">
            <p className="eyebrow">Informação pública, cidadania forte</p>
            <h1>A vida pública merece ser acompanhada de perto.</h1>
            <p className="lede">
              Consulte dados oficiais sobre representantes, mandatos e despesas — com fontes identificadas e informação clara.
            </p>
            <div className="hero-actions">
              <Link className="button button-primary" to="/politicos">
                <IconSearch className="icon" />
                Encontrar um político
              </Link>
              <Link className="button button-secondary" to="/transparencia">
                Explorar despesas públicas
              </Link>
            </div>
            <p className="home-source-note">Apartidário · Fontes públicas · Sem cadastro</p>
          </div>
        </header>

        <aside className="status-card home-status" aria-live="polite">
          <span className="home-status-mark" aria-hidden="true">VT</span>
          <p className="eyebrow">Serviço</p>
          <h2>Status da plataforma</h2>
          {health.state === "loading" && <p role="status">Verificando conexão com os dados...</p>}
          {health.state === "error" && (
            <p className="status-error" role="status">Não foi possível consultar o status da API.</p>
          )}
          {health.state === "ready" && (
            <dl className="status-list">
              <div>
                <dt>API</dt>
                <dd><span className={`status-dot status-${health.data.api.status}`} />{health.data.api.status}</dd>
              </div>
              <div>
                <dt>Banco de dados</dt>
                <dd><span className={`status-dot status-${health.data.database.status}`} />{health.data.database.status}</dd>
              </div>
            </dl>
          )}
        </aside>
      </div>

      <section className="home-explore" aria-labelledby="home-explore-title">
        <div className="home-section-heading">
          <p className="eyebrow">Voto Transparente</p>
          <h2 id="home-explore-title">O que você quer consultar?</h2>
          <p>Escolha uma área para começar. Cada registro acompanha sua origem sempre que disponível.</p>
        </div>
        <ul className="feature-grid">
          <li>
            <Link className="feature-card" to="/politicos">
              <span className="feature-icon"><IconUsers className="icon" /></span>
              <h3>Políticos</h3>
              <p>Pesquise representantes, cargos e trajetória pública.</p>
              <span className="feature-cta">Pesquisar <span aria-hidden="true">→</span></span>
            </Link>
          </li>
          <li>
            <Link className="feature-card" to="/transparencia">
              <span className="feature-icon"><IconBalance className="icon" /></span>
              <h3>Transparência</h3>
              <p>Explore despesas informadas por período e categoria.</p>
              <span className="feature-cta">Ver despesas <span aria-hidden="true">→</span></span>
            </Link>
          </li>
          <li>
            <Link className="feature-card" to="/noticias">
              <span className="feature-icon"><IconNews className="icon" /></span>
              <h3>Notícias</h3>
              <p>Acompanhe a cobertura política com indicação de fontes.</p>
              <span className="feature-cta">Ler notícias <span aria-hidden="true">→</span></span>
            </Link>
          </li>
          <li>
            <Link className="feature-card" to="/colinha">
              <span className="feature-icon"><IconChecklist className="icon" /></span>
              <h3>Colinha eleitoral</h3>
              <p>Organize escolhas e anotações de forma privada.</p>
              <span className="feature-cta">Abrir colinha <span aria-hidden="true">→</span></span>
            </Link>
          </li>
        </ul>
      </section>
    </section>
  );
}

export default HomePage;
