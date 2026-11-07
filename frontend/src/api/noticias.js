import demonstracaoData from './demonstracao.json';

const obterLista = () => {
  if (Array.isArray(demonstracaoData)) return demonstracaoData;
  if (demonstracaoData && Array.isArray(demonstracaoData.noticias)) return demonstracaoData.noticias;
  return [];
};

export async function listarNoticias(params = {}) {
  let lista = obterLista();
  const page = Number(params.page) || 1;
  const per_page = Number(params.per_page) || 10;

  // Filtragem básica se houver parâmetros
  if (params.politico) {
    lista = lista.filter(n => String(n.politico_id) === String(params.politico));
  }
  if (params.veiculo) {
    lista = lista.filter(n => n.veiculo === params.veiculo || n.fonte?.includes(params.veiculo));
  }
  if (params.assunto) {
    lista = lista.filter(n => n.categoria?.toLowerCase() === params.assunto.toLowerCase());
  }

  const total = lista.length;
  const pages = Math.ceil(total / per_page) || 1;
  const start = (page - 1) * per_page;
  const items = lista.slice(start, start + per_page);

  return {
    items,
    total,
    page,
    pages
  };
}

export async function listarVeiculos() {
  const lista = obterLista();
  // Extrai fontes únicas para popular o seletor de veículos/fontes
  const veiculosUnicos = [...new Set(lista.map(n => n.fonte).filter(Boolean))];
  const items = veiculosUnicos.map((nome, index) => ({
    slug: `veiculo-${index}`,
    nome,
    coleta_autorizada: true,
    base_autorizacao: "Portal Oficial de Notícias",
    url_termos: ""
  }));
  return { items };
}

export async function obterFiltrosNoticias() {
  const lista = obterLista();
  const assuntos = [...new Set(lista.map(n => n.categoria).filter(Boolean))].map(cat => ({
    slug: cat.toLowerCase(),
    nome: cat
  }));
  
  return {
    politicos: [],
    veiculos: [],
    assuntos,
    naturezas: [
      { codigo: "fato", rotulo: "Fato Comprovado" },
      { codigo: "alegacao", rotulo: "Alegação" }
    ]
  };
}

export async function obterNoticia(id) {
  const lista = obterLista();
  return lista.find(n => String(n.id) === String(id)) || lista[0];
}

export default {
  listarNoticias,
  listarVeiculos,
  obterFiltrosNoticias,
  obterNoticia
};