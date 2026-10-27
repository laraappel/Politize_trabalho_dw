import { Link } from "react-router-dom";

function NotFoundPage() {
  return (
    <section className="page">
      <header className="page-header">
        <p className="eyebrow">Página não encontrada</p>
        <h1>Não encontramos este endereço.</h1>
        <p className="lede">Verifique o link ou volte para a página inicial.</p>
        <Link className="button button-primary" to="/">
          Ir para o início
        </Link>
      </header>
    </section>
  );
}

export default NotFoundPage;
