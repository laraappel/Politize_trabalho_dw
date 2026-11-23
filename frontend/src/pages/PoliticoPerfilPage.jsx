
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { obterPolitico } from "../api/politicos";
import {
  adicionarNaColinha,
  estaNaColinha,
  removerDaColinha,
} from "../api/colinha";
import NoticiasDoPolitico from "../components/NoticiasDoPolitico";
import DadoAusente from "../components/DadoAusente";
import SeloDemonstracao from "../components/SeloDemonstracao";
import {
  formatarData,
  formatarDinheiro,
  rotuloVoto,
} from "../formatters";

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
      .catch((erro) => {
        if (!ativo) return;

        setEstado({
          status: "error",
          mensagem: erro.message,
          codigo: erro.codigo,
        });
      });

    return () => {
      ativo = false;
    };
  }, [id]);

  if (estado.status === "loading") {
    return (
      <section className="page">
        <p role="status">Carregando perfil do político...</p>
      </section>
    );
  }

  if (estado.status === "error") {
    return (
      <section className="page">
        <header className="page-header">
          <p className="eyebrow">Perfil político</p>

          <h1>
            {estado.codigo === "nao_encontrado"
              ? "Político não encontrado"
              : "Não foi possível abrir o perfil"}
          </h1>

          <p className="lede status-error">
            {estado.mensagem || "Ocorreu um erro ao consultar os dados."}
          </p>

          <Link className="button button-secondary" to="/politicos">
            Voltar à pesquisa
          </Link>
        </header>
      </section>
    );
  }

  const p = estado.data;

  const mandatos = p.mandatos || [];
  const projetos = p.projetos || [];
  const votacoes = p.votacoes || [];
  const despesas = p.despesas || [];
  const financeiro = p.resumo_financeiro || {};
  const categorias = financeiro.por_categoria || [];

  function alternarColinha() {
    if (naColinha) {
      removerDaColinha(p.id);
      setNaColinha(false);
    } else {
      adicionarNaColinha(p);
      setNaColinha(true);
    }
  }

  function Fonte({ registro }) {
    if (!registro?.fonte?.nome && !registro?.origem_dados) {
      return null;
    }

    return (
      <p className="fonte-registro">
        Fonte:{" "}
        {registro.fonte?.url ? (
          <a
            href={registro.fonte.url}
            target="_blank"
            rel="noopener noreferrer"
          >
            {registro.fonte.nome}
          </a>
        ) : (
          registro.fonte?.nome || registro.origem_dados
        )}
      </p>
    );
  }

  return (
    <section className="page politico-perfil">

      {/* PERFIL */}
      <header className="page-header">
        <p className="eyebrow">Perfil do político</p>

        <h1>
          {p.nome_exibicao || (
            <DadoAusente texto="Nome não informado" />
          )}

          <SeloDemonstracao visivel={p.demonstracao} />
        </h1>

        <p className="lede">
          {p.cargo || "Cargo não informado"}
          {p.partido ? ` · ${p.partido}` : ""}
          {p.uf ? ` · ${p.uf}` : ""}
          {p.municipio ? ` · ${p.municipio}` : ""}
        </p>

        <Fonte registro={p} />

        <div className="hero-actions">
          <button
            type="button"
            className="button button-primary"
            onClick={alternarColinha}
          >
            {naColinha
              ? "Remover da colinha"
              : "Adicionar à colinha"}
          </button>

          <Link className="button button-secondary" to="/politicos">
            Voltar à pesquisa
          </Link>
        </div>
      </header>

      {/* MANDATOS */}
      <section>
        <h2>Histórico de mandatos</h2>

        {mandatos.length === 0 ? (
          <p>Não existem mandatos cadastrados para este político.</p>
        ) : (
          <ul className="lista-simples">
            {mandatos.map((m) => (
              <li key={m.id}>
                <strong>{m.cargo || "Cargo não informado"}</strong>

                <p>
                  Esfera: {m.esfera || "Não informada"}
                </p>

                <p>
                  Localidade:{" "}
                  {[m.municipio, m.uf].filter(Boolean).join(" - ") ||
                    "Não informada"}
                </p>

                <p>
                  Partido: {m.partido || "Não informado"}
                </p>

                <p>
                  Período: {formatarData(m.inicio) || "Não informado"}
                  {" — "}
                  {m.em_curso
                    ? "Em curso"
                    : formatarData(m.fim) || "Não informado"}
                </p>

                <Fonte registro={m} />
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* PROPOSTAS */}
      <section>
        <h2>Propostas e compromissos</h2>

        <p>
          Não existem propostas de campanha integradas à API atualmente.
          Portanto, não é possível apresentar ou confirmar o cumprimento
          de compromissos eleitorais.
        </p>
      </section>

      {/* PROJETOS */}
      <section>
        <h2>Projetos legislativos</h2>

        {projetos.length === 0 ? (
          <p>
            Nenhum projeto legislativo cadastrado para este político.
          </p>
        ) : (
          <ul className="lista-simples">
            {projetos.map((pr) => (
              <li key={pr.id}>
                <strong>
                  {pr.identificacao || "Identificação não informada"}
                </strong>

                <p>
                  Ementa:{" "}
                  {pr.ementa || "Ementa não informada"}
                </p>

                <p>
                  Data de apresentação:{" "}
                  {formatarData(pr.data_apresentacao) ||
                    "Data não informada"}
                </p>

                <p>
                  Situação: {pr.situacao || "Situação não informada"}
                </p>

                {pr.url_oficial && (
                  <p>
                    <a
                      href={pr.url_oficial}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Consultar fonte oficial do projeto
                    </a>
                  </p>
                )}

                <Fonte registro={pr} />
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* VOTAÇÕES */}
      <section>
        <h2>Votações</h2>

        {votacoes.length === 0 ? (
          <p>
            Nenhuma votação individual cadastrada para este político.
          </p>
        ) : (
          <ul className="lista-simples">
            {votacoes.map((v) => (
              <li key={v.id}>
                <strong>
                  {formatarData(v.data_votacao) ||
                    "Data não informada"}
                </strong>

                <p>
                  Matéria: {v.ementa || "Ementa não informada"}
                </p>

                <p>
                  Voto individual:{" "}
                  {rotuloVoto(v.voto) || "Voto não informado"}
                </p>

                {v.url_oficial && (
                  <p>
                    <a
                      href={v.url_oficial}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Consultar registro oficial da votação
                    </a>
                  </p>
                )}

                <Fonte registro={v} />
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* TRANSPARÊNCIA FINANCEIRA */}
      <section>
        <h2>Transparência financeira</h2>

        <p>
          Esta seção apresenta despesas relacionadas ao mandato.
          Elas não representam salário ou remuneração pessoal do político.
        </p>

        {financeiro.registros === 0 || despesas.length === 0 ? (
          <p>
            Não existem despesas cadastradas. Isso não significa que
            os gastos sejam iguais a zero.
          </p>
        ) : (
          <>
            <h3>Resumo financeiro</h3>

            <p>
              Registros encontrados: {financeiro.registros}
            </p>

            <p>
              Valores informados:{" "}
              {formatarDinheiro(financeiro.soma_valores_informados) ||
                "Nenhum valor disponível"}
            </p>

            <p>
              Registros sem valor:{" "}
              {financeiro.registros_sem_valor ?? "Não informado"}
            </p>

            <p>
              {financeiro.completo
                ? "Todos os registros possuem valores informados."
                : "Existem registros sem valores. A ausência de informação não foi tratada como zero."}
            </p>

            {/* DESPESAS POR CATEGORIA */}
            <h3>Despesas por categoria</h3>

            {categorias.length === 0 ? (
              <p>
                Não existem informações agrupadas por categoria.
              </p>
            ) : (
              <ul className="lista-simples">
                {categorias.map((categoria) => (
                  <li key={categoria.categoria}>
                    <strong>{categoria.categoria}</strong>

                    <p>
                      Quantidade de registros: {categoria.registros}
                    </p>

                    <p>
                      Total informado:{" "}
                      {formatarDinheiro(
                        categoria.soma_valores_informados
                      ) || "Valor não disponível"}
                    </p>

                    <p>
                      Registros sem valor:{" "}
                      {categoria.registros_sem_valor}
                    </p>
                  </li>
                ))}
              </ul>
            )}

            {/* LISTA DE DESPESAS */}
            <h3>Registros de despesas</h3>

            <ul className="lista-simples">
              {despesas.map((d) => (
                <li key={d.id}>
                  <strong>
                    {d.categoria || "Categoria não informada"}
                  </strong>

                  <p>
                    Descrição:{" "}
                    {d.descricao || "Descrição não informada"}
                  </p>

                  <p>
                    Período:{" "}
                    {formatarData(d.periodo?.inicio) ||
                      "Não informado"}
                    {" — "}
                    {formatarData(d.periodo?.fim) ||
                      "Não informado"}
                  </p>

                  <p>
                    Valor:{" "}
                    {formatarDinheiro(d.valor) ||
                      "Valor não informado"}
                  </p>

                  <Fonte registro={d} />
                </li>
              ))}
            </ul>
          </>
        )}

        <h3>Outras informações financeiras</h3>

        <p>
          Remuneração, benefícios e patrimônio declarado não estão
          disponíveis na integração atual.
        </p>
      </section>

      {/* NOTÍCIAS */}
      <section>
        <h2>Notícias relacionadas</h2>

        <NoticiasDoPolitico politicoId={p.id} />
      </section>

    </section>
  );
}

export default PoliticoPerfilPage;
