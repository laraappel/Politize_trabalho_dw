import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { listarCargosEletivos, obterFiltrosCargosEletivos } from "../api/cargos";
import {
  adicionarCandidaturaNaColinha,
  atualizarAnotacao,
  chaveCandidatura,
  chaveEscolha,
  lerColinha,
  limparColinha,
  removerDaColinha,
  substituirCandidaturaNaColinha,
} from "../api/colinha";

function ColinhaPage() {
  const [dados, setDados] = useState(() => lerColinha());
  const [opcoes, setOpcoes] = useState({ anos: [], cargos: [], ufs: [], partidos: [] });
  const [filtros, setFiltros] = useState({ ano: "", cargo: "", uf: "", municipio: "", partido: "", q: "" });
  const [resultado, setResultado] = useState({ items: [], total: 0, page: 1, pages: 0 });
  const [estadoBusca, setEstadoBusca] = useState("loading");
  const [mensagem, setMensagem] = useState("");
  const [alvoEdicao, setAlvoEdicao] = useState(null);

  async function consultarCandidatos(parametros, pagina = 1) {
    setEstadoBusca("loading");
    setMensagem("");
    try {
      const resposta = await listarCargosEletivos({ ...parametros, page: pagina, per_page: 50 });
      setResultado(resposta);
      setEstadoBusca("ready");
    } catch (erro) {
      setMensagem(erro.message || "Não foi possível consultar os candidatos.");
      setEstadoBusca("error");
    }
  }

  useEffect(() => {
    let ativo = true;
    obterFiltrosCargosEletivos()
      .then((filtrosDisponiveis) => {
        if (!ativo) return;
        const iniciais = {
          ano: String(filtrosDisponiveis.anos?.[0] || ""),
          cargo: "",
          uf: "",
          municipio: "",
          partido: "",
          q: "",
        };
        setOpcoes(filtrosDisponiveis);
        setFiltros(iniciais);
        consultarCandidatos(iniciais);
      })
      .catch((erro) => {
        if (!ativo) return;
        setMensagem(erro.message || "Não foi possível carregar os filtros eleitorais.");
        setEstadoBusca("error");
      });
    return () => { ativo = false; };
  }, []);

  const grupos = useMemo(() => {
    const agrupados = new Map();
    dados.itens.forEach((item) => {
      const ano = item.anoEleicao ? String(item.anoEleicao) : "Eleição não informada";
      const cargo = item.cargo || "Cargo não informado";
      const chave = `${ano}|${cargo}`;
      if (!agrupados.has(chave)) agrupados.set(chave, { ano, cargo, itens: [] });
      agrupados.get(chave).itens.push(item);
    });
    return [...agrupados.values()].sort((a, b) =>
      b.ano.localeCompare(a.ano, "pt-BR", { numeric: true }) || a.cargo.localeCompare(b.cargo, "pt-BR")
    );
  }, [dados.itens]);

  function atualizarFiltro(evento) {
    setFiltros((atuais) => ({ ...atuais, [evento.target.name]: evento.target.value }));
  }

  function salvarLocal(operacao) {
    try {
      setDados(operacao());
      setMensagem("");
    } catch {
      setMensagem("Não foi possível salvar neste navegador. Verifique o espaço disponível ou as permissões de armazenamento.");
    }
  }

  function escolher(candidato) {
    const novaChave = chaveCandidatura(candidato);
    if (dados.itens.some((item) => chaveEscolha(item) === novaChave && chaveEscolha(item) !== alvoEdicao)) {
      setMensagem("Esse candidato já está na sua colinha.");
      return;
    }
    salvarLocal(() => alvoEdicao
      ? substituirCandidaturaNaColinha(alvoEdicao, candidato)
      : adicionarCandidaturaNaColinha(candidato));
    setAlvoEdicao(null);
  }

  function iniciarTroca(item) {
    const chave = chaveEscolha(item);
    setAlvoEdicao(chave);
    const filtrosDaEscolha = {
      ...filtros,
      ano: String(item.anoEleicao || ""),
      cargo: item.cargo || "",
      uf: item.uf || "",
      municipio: item.municipio || "",
      partido: "",
      q: "",
    };
    setFiltros(filtrosDaEscolha);
    consultarCandidatos(filtrosDaEscolha);
    document.getElementById("colinha-busca")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function enviarBusca(evento) {
    evento.preventDefault();
    setAlvoEdicao(null);
    consultarCandidatos(filtros);
  }

  function limparLista() {
    if (window.confirm("Remover todas as escolhas e anotações salvas neste navegador?")) {
      salvarLocal(limparColinha);
      setAlvoEdicao(null);
    }
  }

  return (
    <section className="page colinha-pagina">
      <header className="page-header">
        <p className="eyebrow">Colinha eleitoral</p>
        <h1>Monte sua colinha eleitoral</h1>
        <p className="lede">
          Consulte candidatos, escolha seus nomes por eleição e cargo, e mantenha suas anotações privadas.
        </p>
      </header>

      <div className="notice colinha-aviso" role="note">
        <strong>Privacidade:</strong> suas escolhas e anotações ficam apenas no armazenamento local deste navegador;
        não exigem cadastro e não são enviadas ao servidor. A busca consulta dados públicos já importados do TSE
        (candidatos eleitos de 2022 e 2024). Esta lista não registra voto oficial.
      </div>

      <section id="colinha-busca" className="colinha-busca" aria-labelledby="colinha-busca-titulo">
        <div>
          <p className="eyebrow">Pesquisa eleitoral</p>
          <h2 id="colinha-busca-titulo">Encontre um candidato</h2>
        </div>
        <form className="colinha-filtros" onSubmit={enviarBusca}>
          <label>
            Eleição
            <select name="ano" value={filtros.ano} onChange={atualizarFiltro}>
              <option value="">Todas</option>
              {opcoes.anos.map((ano) => <option key={ano} value={ano}>{ano}</option>)}
            </select>
          </label>
          <label>
            Cargo
            <select name="cargo" value={filtros.cargo} onChange={atualizarFiltro}>
              <option value="">Todos</option>
              {opcoes.cargos.map((cargo) => <option key={cargo} value={cargo}>{cargo}</option>)}
            </select>
          </label>
          <label>
            UF
            <select name="uf" value={filtros.uf} onChange={atualizarFiltro}>
              <option value="">Todas</option>
              {opcoes.ufs.map((uf) => <option key={uf} value={uf}>{uf}</option>)}
            </select>
          </label>
          <label>
            Município
            <input name="municipio" value={filtros.municipio} onChange={atualizarFiltro} placeholder="Ex.: Florianópolis" />
          </label>
          <label>
            Partido
            <select name="partido" value={filtros.partido} onChange={atualizarFiltro}>
              <option value="">Todos</option>
              {opcoes.partidos.map((partido) => <option key={partido} value={partido}>{partido}</option>)}
            </select>
          </label>
          <label className="colinha-termo">
            Nome ou número
            <input name="q" value={filtros.q} onChange={atualizarFiltro} placeholder="Digite o nome ou número de urna" />
          </label>
          <div className="colinha-busca-acoes">
            <button type="submit" className="button button-primary" disabled={estadoBusca === "loading"}>
              {estadoBusca === "loading" ? "Buscando…" : "Buscar candidatos"}
            </button>
            {alvoEdicao && (
              <button type="button" className="button button-secondary" onClick={() => setAlvoEdicao(null)}>
                Cancelar troca
              </button>
            )}
          </div>
        </form>

        {alvoEdicao && <p className="colinha-status" role="status">Escolha outro candidato para substituir a seleção; sua anotação será mantida.</p>}
        {estadoBusca === "error" && <p className="status-error" role="alert">{mensagem}</p>}
        {estadoBusca === "loading" && <p role="status">Consultando candidatos…</p>}
        {estadoBusca === "ready" && (
          <>
            <p className="colinha-contagem">{resultado.total} candidato(s) encontrado(s).</p>
            {resultado.items.length === 0 ? (
              <p>Nenhum candidato encontrado com esses filtros. Ajuste a busca e tente novamente.</p>
            ) : (
              <ul className="colinha-resultados">
                {resultado.items.map((candidato) => {
                  const chave = chaveCandidatura(candidato);
                  const jaEscolhido = dados.itens.some((item) => chaveEscolha(item) === chave);
                  const local = [candidato.municipio, candidato.uf].filter(Boolean).join(" · ");
                  return (
                    <li key={candidato.id} className="colinha-candidato">
                      <div>
                        <h3><Link to={`/politicos/${candidato.politico_id}`}>{candidato.nome}</Link></h3>
                        <p className="colinha-detalhes">
                          <span>{candidato.cargo}</span>
                          {candidato.numero_candidato && <span>Número {candidato.numero_candidato}</span>}
                          {candidato.partido && <span>{candidato.partido}</span>}
                          {local && <span>{local}</span>}
                          <span>{candidato.ano_eleicao}</span>
                        </p>
                      </div>
                      <button
                        type="button"
                        className={jaEscolhido ? "button button-secondary" : "button button-primary"}
                        disabled={jaEscolhido}
                        onClick={() => escolher(candidato)}
                      >
                        {alvoEdicao ? (jaEscolhido ? "Já está na colinha" : "Substituir escolha") : (jaEscolhido ? "Na colinha" : "Adicionar")}
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
            {resultado.pages > 1 && (
              <nav className="colinha-paginacao" aria-label="Paginação dos candidatos">
                <button type="button" className="button button-secondary" disabled={resultado.page <= 1 || estadoBusca === "loading"} onClick={() => consultarCandidatos(filtros, resultado.page - 1)}>Anterior</button>
                <span>Página {resultado.page} de {resultado.pages}</span>
                <button type="button" className="button button-secondary" disabled={resultado.page >= resultado.pages || estadoBusca === "loading"} onClick={() => consultarCandidatos(filtros, resultado.page + 1)}>Próxima</button>
              </nav>
            )}
          </>
        )}
      </section>

      <section className="colinha-salva" aria-labelledby="colinha-salva-titulo">
        <div className="colinha-lista-cabecalho">
          <div>
            <p className="eyebrow">Neste navegador</p>
            <h2 id="colinha-salva-titulo">Minhas escolhas <span>({dados.itens.length})</span></h2>
          </div>
          {dados.itens.length > 0 && (
            <div className="colinha-acoes">
              <button type="button" className="button button-secondary colinha-nao-imprimir" onClick={() => window.print()}>Imprimir lista</button>
              <button type="button" className="button button-secondary colinha-nao-imprimir" onClick={limparLista}>Limpar colinha</button>
            </div>
          )}
        </div>

        {mensagem && estadoBusca !== "error" && <p className="status-error" role="alert">{mensagem}</p>}
        {grupos.length === 0 ? (
          <p className="colinha-vazia">Sua lista ainda está vazia. Use a pesquisa acima para adicionar candidatos.</p>
        ) : grupos.map((grupo) => (
          <section className="colinha-grupo" key={`${grupo.ano}|${grupo.cargo}`}>
            <h3>{grupo.ano} <span>·</span> {grupo.cargo}</h3>
            <ul className="colinha-escolhas">
              {grupo.itens.map((item) => {
                const chave = chaveEscolha(item);
                return (
                  <li className="colinha-escolha" key={chave}>
                    <div className="colinha-escolha-cabecalho">
                      <div>
                        <h4><Link to={`/politicos/${item.politicoId}`}>{item.nome}</Link></h4>
                        <p className="colinha-detalhes">
                          {item.numero && <span>Número {item.numero}</span>}
                          {item.partido && <span>{item.partido}</span>}
                          {[item.municipio, item.uf].filter(Boolean).length > 0 && <span>{[item.municipio, item.uf].filter(Boolean).join(" · ")}</span>}
                        </p>
                      </div>
                      <div className="colinha-acoes colinha-nao-imprimir">
                        <button type="button" className="button button-secondary" onClick={() => iniciarTroca(item)}>Trocar candidato</button>
                        <button type="button" className="button button-secondary" onClick={() => salvarLocal(() => removerDaColinha(chave))}>Remover</button>
                      </div>
                    </div>
                    <label className="colinha-anotacao">
                      Anotação privada
                      <textarea
                        rows={2}
                        maxLength={2000}
                        value={item.anotacao || ""}
                        onChange={(evento) => salvarLocal(() => atualizarAnotacao(chave, evento.target.value))}
                        placeholder="Escreva um lembrete (opcional)"
                      />
                    </label>
                  </li>
                );
              })}
            </ul>
          </section>
        ))}
      </section>
    </section>
  );
}

export default ColinhaPage;
