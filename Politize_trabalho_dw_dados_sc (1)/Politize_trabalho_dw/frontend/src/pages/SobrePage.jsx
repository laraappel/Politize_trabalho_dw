function SobrePage() {
  return (
    <section className="page">
      <header className="page-header">
        <p className="eyebrow">Sobre o projeto</p>
        <h1>Voto Transparente</h1>
        <p className="lede">
          Plataforma brasileira de transparência política, educação cidadã e
          acompanhamento eleitoral. O projeto é apartidário e baseado em informações
          verificáveis.
        </p>
      </header>

      <div className="prose">
        <h2>Princípios</h2>
        <ul>
          <li>Apartidarismo: nenhuma identidade visual ou conteúdo favorece partidos.</li>
          <li>Acessibilidade: interface legível, navegação por teclado e textos claros.</li>
          <li>Verificabilidade: dados devem apontar para fontes oficiais ou públicas.</li>
        </ul>

        <h2>Fontes previstas</h2>
        <p>
          Integrações eleitorais e coleta automática de notícias ainda não fazem parte
          desta etapa. As fontes candidatas incluem portais oficiais de transparência,
          dados abertos do Congresso, TSE e diários oficiais.
        </p>
      </div>
    </section>
  );
}

export default SobrePage;
