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

export function removerDaColinha(politicoId) {
  const dados = lerColinha();
  dados.itens = dados.itens.filter((item) => item.politicoId !== Number(politicoId));
  return gravar(dados);
}

export function atualizarAnotacao(politicoId, anotacao) {
  const dados = lerColinha();
  dados.itens = dados.itens.map((item) =>
    item.politicoId === Number(politicoId) ? { ...item, anotacao: anotacao.slice(0, 2000) } : item
  );
  return gravar(dados);
}

export function limparColinha() {
  return gravar(vazio());
}
