import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getHealth } from "../../api/client";

function Footer() {
  const [health, setHealth] = useState({ state: "loading" });

  useEffect(() => {
    getHealth()
      .then((data) => setHealth({ state: "ready", data }))
      .catch(() => setHealth({ state: "error" }));
  }, []);

  return (
    <footer className="site-footer">
      <div className="footer-inner">
        <section className="footer-about" aria-labelledby="footer-about-title">
          <div>
            <p className="footer-eyebrow">Sobre o serviço</p>
            <h2 id="footer-about-title">Voto Transparente</h2>
          </div>
          <p>
            Uma plataforma apartidária para consultar informações públicas sobre
            representantes, mandatos, despesas e notícias, aproximando dados e
            cidadania.
          </p>
          <Link to="/sobre">Conheça o projeto <span aria-hidden="true">→</span></Link>
        </section>
        <section className="footer-status" aria-label="Status da plataforma" aria-live="polite">
          <strong>Status da plataforma</strong>
          {health.state === "loading" && <span role="status">Verificando conexão...</span>}
          {health.state === "error" && (
            <span className="footer-status-error" role="status">Não foi possível consultar a API.</span>
          )}
          {health.state === "ready" && (
            <>
              <span className="footer-status-item">
                <span className={`status-dot status-${health.data.api.status}`} />
                API: {health.data.api.status}
              </span>
              <span className="footer-status-item">
                <span className={`status-dot status-${health.data.database.status}`} />
                Banco de dados: {health.data.database.status}
              </span>
            </>
          )}
        </section>
        <div className="footer-notes">
          <p>Projeto estudantil de transparência política e educação cidadã.</p>
          <p>
            Dados de demonstração são fictícios e identificados na interface. Consulte
            <Link to="/sobre"> fontes e limitações</Link>.
          </p>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
