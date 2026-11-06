import demonstracaoData from './demonstracao.json';

const obterDados = () => {
  return Array.isArray(demonstracaoData) ? demonstracaoData : demonstracaoData.noticias || [];
};

// Exportações para cobrir todas as variantes de nomes que os teus componentes usam
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
  getNoticias,
  obterNoticias,
  obterNoticia,
  getNoticiaById
};