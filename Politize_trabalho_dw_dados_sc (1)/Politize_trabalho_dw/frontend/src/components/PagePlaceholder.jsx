function PagePlaceholder({ title, description, children }) {
  return (
    <section className="page">
      <header className="page-header">
        <p className="eyebrow">Em desenvolvimento</p>
        <h1>{title}</h1>
        <p className="lede">{description}</p>
      </header>
      <div className="notice" role="status">
        Esta funcionalidade ainda não está disponível. A estrutura da página já existe
        para o time implementar o módulo sem alterar o restante da navegação.
      </div>
      {children}
    </section>
  );
}

export default PagePlaceholder;
