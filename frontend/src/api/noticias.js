import demonstracaoData from './demonstracao.json';

const obterDados = () => {
  return Array.isArray(demonstracaoData) ? demonstracaoData : demonstracaoData.noticias || [];
};

// Exportações para cobrir todas as funções chamadas pelos componentes do projeto
export async function listarNoticiasDoPolitico() {
  return obterDados();
}

export async function obterFiltrosNoticias() {
  const lista = obterDados();
  const categorias = [...new Set(lista.map(n => n.categoria).filter(Boolean))];
  return { categorias };
}

export async function listarVeiculos() {
  return obterDados();
}

export async function listarNoticias() {
  return obterDados();
}

export async function getNoticias() {
  return obterDados();
}

export async function obterNoticias() {
  return obterDados();
}

export async function obterNoticia(id) {
  const lista = obterDados();
  return lista.find(n => String(n.id) === String(id)) || lista[0];
}

export async function getNoticiaById(id) {
  const lista = obterDados();
  return lista.find(n => String(n.id) === String(id)) || lista[0];
}

export default {
  listarNoticiasDoPolitico,
  obterFiltrosNoticias,
  listarVeiculos,
  listarNoticias,
  getNoticias,
  obterNoticias,
  obterNoticia,
  getNoticiaById
};