const CHAVE = "voto-transparente-colinha-v1";

function vazio() {
  return { versao: 1, itens: [] };
}

export function lerColinha() {
  try {
    const bruto = localStorage.getItem(CHAVE);
    if (!bruto) return vazio();
    const dados = JSON.parse(bruto);
    if (!dados || !Array.isArray(dados.itens)) return vazio();
    return { versao: 1, itens: dados.itens };
  } catch {
    return vazio();
  }
}

function gravar(dados) {
  localStorage.setItem(CHAVE, JSON.stringify(dados));
  return dados;
}

export function estaNaColinha(politicoId) {
  const id = Number(politicoId);
  return lerColinha().itens.some((item) => item.politicoId === id);
}

export function adicionarNaColinha(politico) {
  const dados = lerColinha();
  const id = Number(politico.id);
  if (dados.itens.some((item) => item.politicoId === id)) return dados;
  dados.itens.push({
    politicoId: id,
    nome: politico.nome_exibicao || politico.nome_completo,
    cargo: politico.cargo || "",
    partido: politico.partido || "",
    uf: politico.uf || "",
    anotacao: "",
    prioridade: dados.itens.length + 1,
  });
  return gravar(dados);
}

export function chaveEscolha(item) {
  return item.chave || String(item.politicoId);
}

export function chaveCandidatura(candidato) {
  const ano = Number(candidato.ano_eleicao);
  const politicoId = Number(candidato.politico_id);
  const cargo = candidato.cargo || "Cargo não informado";
  const uf = candidato.uf || "";
  const municipio = candidato.municipio || "";
  return [ano, cargo, uf, municipio, politicoId].join("|");
}

function dadosEscolha(candidato) {
  const chave = chaveCandidatura(candidato);
  const ano = Number(candidato.ano_eleicao);
  const politicoId = Number(candidato.politico_id);
  const cargo = candidato.cargo || "Cargo não informado";
  const uf = candidato.uf || "";
  const municipio = candidato.municipio || "";

  return {
    chave,
    politicoId,
    anoEleicao: ano,
    cargo,
    uf,
    municipio,
    nome: candidato.nome || "Nome não informado",
    numero: candidato.numero_candidato || "",
    partido: candidato.partido || "",
    situacao: candidato.situacao || "",
    fonte: candidato.fonte?.nome || "",
    fonteUrl: candidato.fonte?.url || "",
    anotacao: "",
  };
}

export function adicionarCandidaturaNaColinha(candidato) {
  const dados = lerColinha();
  const escolha = dadosEscolha(candidato);
  if (dados.itens.some((item) => chaveEscolha(item) === escolha.chave)) return dados;
  dados.itens.push(escolha);
  return gravar(dados);
}

export function substituirCandidaturaNaColinha(chave, candidato) {
  const dados = lerColinha();
  const indice = dados.itens.findIndex((item) => chaveEscolha(item) === chave);
  if (indice < 0) return dados;

  const escolha = dadosEscolha(candidato);
  if (dados.itens.some((item, index) => index !== indice && chaveEscolha(item) === escolha.chave)) {
    return dados;
  }

  escolha.anotacao = dados.itens[indice].anotacao || "";
  dados.itens[indice] = escolha;
  return gravar(dados);
}

export function removerDaColinha(politicoId) {
  const dados = lerColinha();
  dados.itens = dados.itens.filter((item) =>
    typeof politicoId === "string" && item.chave
      ? item.chave !== politicoId
      : item.politicoId !== Number(politicoId)
  );
  return gravar(dados);
}

export function atualizarAnotacao(politicoId, anotacao) {
  const dados = lerColinha();
  dados.itens = dados.itens.map((item) =>
    chaveEscolha(item) === politicoId || item.politicoId === Number(politicoId)
      ? { ...item, anotacao: anotacao.slice(0, 2000) }
      : item
  );
  return gravar(dados);
}

export function limparColinha() {
  return gravar(vazio());
}
