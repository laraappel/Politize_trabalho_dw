import { Link } from "react-router-dom";

function Footer() {
  return (
    <footer className="site-footer">
      <div className="footer-inner">
        <p>
          <strong>Voto Transparente</strong> é um projeto estudantil apartidário de
          transparência política e educação cidadã.
        </p>
        <p>
          Dados de demonstração são fictícios e identificados na interface. Consulte
          a página <Link to="/sobre">Sobre</Link> para fontes e limitações.
        </p>
      </div>
    </footer>
  );
}

export default Footer;
