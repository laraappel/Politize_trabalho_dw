function SeloDemonstracao({ visivel }) {
  if (!visivel) return null;
  return (
    <span className="selo-demonstracao" title="Este registro é fictício e serve só para testes da plataforma">
      Demonstração
    </span>
  );
}

export default SeloDemonstracao;
