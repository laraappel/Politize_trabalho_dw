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

        <h2>Fontes e dados</h2>
        <p>
          O cadastro inicial usa um conjunto de demonstração, identificado na interface.
          Notícias reais só entram a partir de fontes com autorização documentada
          (hoje, a Agência Brasil). Dados oficiais futuros devem trazer nome e URL da fonte.
        </p>
        <p>
          A colinha eleitoral não sai deste navegador. Não há conta de usuário nesta etapa.
        </p>
      </div>
    </section>
  );
}

export default SobrePage;
