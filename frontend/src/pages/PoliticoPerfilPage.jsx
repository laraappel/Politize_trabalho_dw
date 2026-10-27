import { useParams } from "react-router-dom";
import PagePlaceholder from "../components/PagePlaceholder";

function PoliticoPerfilPage() {
  const { id } = useParams();

  return (
    <PagePlaceholder
      title="Perfil do político"
      description="A ficha individual mostrará cargos, mandatos, propostas, votações e dados patrimoniais."
    >
      <p>
        Identificador solicitado: <strong>{id}</strong>
      </p>
    </PagePlaceholder>
  );
}

export default PoliticoPerfilPage;
