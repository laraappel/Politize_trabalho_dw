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
          As informações futuras serão baseadas em fontes oficiais e públicas. Consulte
          a página <Link to="/sobre">Sobre</Link> para conhecer o propósito e as fontes
          previstas.
        </p>
      </div>
    </footer>
  );
}

export default Footer;
