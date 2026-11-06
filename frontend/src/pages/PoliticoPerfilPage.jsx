import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { obterPolitico } from "../api/politicos";
import { adicionarNaColinha, estaNaColinha, removerDaColinha } from "../api/colinha";
import NoticiasDoPolitico from "../components/NoticiasDoPolitico";
import DadoAusente from "../components/DadoAusente";
import SeloDemonstracao from "../components/SeloDemonstracao";
import { formatarData, formatarDinheiro, rotuloVoto } from "../formatters";

function PoliticoPerfilPage() {
  const { id } = useParams();
  const [estado, setEstado] = useState({ status: "loading" });
  const [naColinha, setNaColinha] = useState(false);

  useEffect(() => {
    let ativo = true;
    setEstado({ status: "loading" });
    obterPolitico(id)
      .then((data) => {
        if (!ativo) return;
        setEstado({ status: "ready", data });
        setNaColinha(estaNaColinha(data.id));
      })
      .catch((erro) => ativo && setEstado({ status: "error", mensagem: erro.message, codigo: erro.codigo }));
    return () => {
      ativo = false;
    };
  }, [id]);

  if (estado.status === "loading") {
    return <p role="status">Carregando perfil…</p>;
  }
  if (estado.status === "error") {
    return (
      <section className="page">
        <header className="page-header">
          <p className="eyebrow">Perfil</p>
          <h1>{estado.codigo === "nao_encontrado" ? "Político não encontrado" : "Não foi possível abrir o perfil"}</h1>
          <p className="lede status-error">{estado.mensagem}</p>
          <Link className="button button-secondary" to="/politicos">Voltar à pesquisa</Link>
        </header>
      </section>
    );
  }

  const p = estado.data;
  const financeiro = p.resumo_financeiro || {};

  function alternarColinha() {
    if (naColinha) {
      removerDaColinha(p.id);
      setNaColinha(false);
    } else {
      adicionarNaColinha(p);
      setNaColinha(true);
    }
  }

  return (
    <section className="page politico-perfil">
      <header className="page-header">
        <p className="eyebrow">Perfil</p>
        <h1>
          {p.nome_exibicao}
          <SeloDemonstracao visivel={p.demonstracao} />
        </h1>
        <p className="lede">
          {p.cargo || <DadoAusente texto="Cargo não informado" />}
          {p.partido ? ` · ${p.partido}` : ""}
          {p.uf ? ` · ${p.uf}` : ""}
          {p.municipio ? ` · ${p.municipio}` : ""}
        </p>
        {p.fonte?.nome && (
          <p className="fonte-registro">
            Fonte: {p.fonte.url ? <a href={p.fonte.url} target="_blank" rel="noopener noreferrer">{p.fonte.nome}</a> : p.fonte.nome}
          </p>
        )}
        <div className="hero-actions">
          <button type="button" className="button button-primary" onClick={alternarColinha}>
            {naColinha ? "Remover da colinha" : "Adicionar à colinha"}
          </button>
          <Link className="button button-secondary" to="/politicos">Voltar à pesquisa</Link>
        </div>
      </header>

      <section>
        <h2>Mandatos</h2>
        {p.mandatos.length === 0 ? (
          <p>Nenhum mandato cadastrado.</p>
        ) : (
          <ul className="lista-simples">
            {p.mandatos.map((m) => (
              <li key={m.id}>
                <strong>{m.cargo}</strong> ({m.esfera}
                {m.uf ? ` · ${m.uf}` : ""}
                {m.municipio ? ` · ${m.municipio}` : ""})
                {" · "}
                {formatarData(m.inicio) || <DadoAusente />}
                {" — "}
                {m.em_curso ? "em curso" : formatarData(m.fim) || <DadoAusente />}
                {m.partido ? ` · ${m.partido}` : ""}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2>Projetos</h2>
        {p.projetos.length === 0 ? (
          <p>Nenhum projeto cadastrado para este perfil.</p>
        ) : (
          <ul className="lista-simples">
            {p.projetos.map((pr) => (
              <li key={pr.id}>
                <strong>{pr.identificacao || "Identificação não informada"}</strong>
                {pr.situacao ? ` · ${pr.situacao}` : ""}
                {pr.data_apresentacao ? ` · ${formatarData(pr.data_apresentacao)}` : ""}
                <p>{pr.ementa || <DadoAusente texto="Ementa não informada" />}</p>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2>Votações</h2>
        {p.votacoes.length === 0 ? (
          <p>Nenhuma votação cadastrada.</p>
        ) : (
          <ul className="lista-simples">
            {p.votacoes.map((v) => (
              <li key={v.id}>
                {formatarData(v.data_votacao) || <DadoAusente texto="Data não informada" />}
                {" · voto: "}
                {rotuloVoto(v.voto) || <DadoAusente texto="voto não informado" />}
                <p>{v.ementa || <DadoAusente texto="Ementa não informada" />}</p>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2>Despesas</h2>
        {financeiro.registros === 0 ? (
          <p>Nenhuma despesa cadastrada. Isso não significa que o gasto seja zero.</p>
        ) : (
          <>
            <p>
              {financeiro.completo
                ? `Valores informados: ${formatarDinheiro(financeiro.soma_valores_informados)}.`
                : `Há ${financeiro.registros_sem_valor} registro(s) sem valor. Soma apenas do que foi informado: ${formatarDinheiro(financeiro.soma_valores_informados) || "nenhum valor disponível"}. A ausência não foi tratada como zero.`}
            </p>
            <ul className="lista-simples">
              {p.despesas.map((d) => (
                <li key={d.id}>
                  <strong>{d.categoria}</strong>
                  {" · "}
                  {formatarData(d.periodo.inicio)} — {formatarData(d.periodo.fim)}
                  {" · "}
                  {formatarDinheiro(d.valor) || <DadoAusente texto="valor não informado" />}
                  <p>{d.descricao}</p>
                </li>
              ))}
            </ul>
          </>
        )}
      </section>

      <NoticiasDoPolitico politicoId={p.id} />
    </section>
  );
}

export default PoliticoPerfilPage;
