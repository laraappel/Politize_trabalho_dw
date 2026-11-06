import demonstracaoData from './demonstracao.json';

const obterDados = () => {
  return Array.isArray(demonstracaoData) ? demonstracaoData : demonstracaoData.noticias || [];
};

// Exportações para resolver todas as chamadas de funções nos componentes
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
  listarVeiculos,
  listarNoticias,
  getNoticias,
  obterNoticias,
  obterNoticia,
  getNoticiaById
};