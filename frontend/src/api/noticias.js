import demonstracaoData from './demonstracao.json';

const obterDados = () => {
  return Array.isArray(demonstracaoData) ? demonstracaoData : demonstracaoData.noticias || [];
};

// Exportação da função de filtros solicitada pela página
export async function obterFiltrosNoticias() {
  const lista = obterDados();
  // Retorna categorias ou filtros únicos extraídos das notícias
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
  obterFiltrosNoticias,
  listarVeiculos,
  listarNoticias,
  getNoticias,
  obterNoticias,
  obterNoticia,
  getNoticiaById
};