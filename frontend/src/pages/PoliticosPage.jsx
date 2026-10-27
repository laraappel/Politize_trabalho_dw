import { Link } from "react-router-dom";
import PagePlaceholder from "../components/PagePlaceholder";

function PoliticosPage() {
  return (
    <PagePlaceholder
      title="Pesquisa de políticos"
      description="A busca por nome, cargo, partido e unidade da federação será implementada neste módulo."
    >
      <p>
        Exemplo de rota de perfil já disponível:{" "}
        <Link to="/politicos/exemplo">/politicos/exemplo</Link>
      </p>
    </PagePlaceholder>
  );
}

export default PoliticosPage;
