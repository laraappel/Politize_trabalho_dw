import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { atualizarAnotacao, lerColinha, limparColinha, removerDaColinha } from "../api/colinha";

function ColinhaPage() {
  const [versao, setVersao] = useState(0);
  const dados = useMemo(() => lerColinha(), [versao]);

  function atualizar() {
    setVersao((n) => n + 1);
  }

  return (
    <section className="page colinha-pagina">
      <header className="page-header">
        <p className="eyebrow">Colinha eleitoral</p>
        <h1>Suas anotações de voto</h1>
        <p className="lede">
          Esta lista fica apenas neste navegador. Nada é enviado ao servidor nem publicado.
        </p>
      </header>

      <div className="notice" role="note">
        Use a colinha para organizar lembretes privados. Ela não substitui o título de eleitor nem
        registra voto oficial.
      </div>

      {dados.itens.length === 0 ? (
        <p>
          Sua colinha está vazia. Abra um{" "}
          <Link to="/politicos">perfil de político</Link> e use “Adicionar à colinha”.
        </p>
      ) : (
        <>
          <p>
            <button type="button" className="button button-secondary" onClick={() => { limparColinha(); atualizar(); }}>
              Limpar colinha neste navegador
            </button>
          </p>
          <ul className="lista-simples">
            {dados.itens.map((item) => (
              <li key={item.politicoId} className="colinha-item">
                <h2>
                  <Link to={`/politicos/${item.politicoId}`}>{item.nome}</Link>
                </h2>
                <p>
                  {[item.cargo, item.partido, item.uf].filter(Boolean).join(" · ") || "Sem cargo informado"}
                </p>
                <label>
                  Anotação privada
                  <textarea
                    rows={3}
                    maxLength={2000}
                    defaultValue={item.anotacao}
                    onBlur={(e) => {
                      atualizarAnotacao(item.politicoId, e.target.value);
                      atualizar();
                    }}
                  />
                </label>
                <p>
                  <button type="button" className="button button-secondary" onClick={() => { removerDaColinha(item.politicoId); atualizar(); }}>
                    Remover
                  </button>
                </p>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}

export default ColinhaPage;
