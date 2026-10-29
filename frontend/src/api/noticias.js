import { API_URL } from "./client";

async function getJson(path, params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") query.set(key, value);
  });
  const suffix = query.toString() ? `?${query}` : "";
  const response = await fetch(`${API_URL}/api${path}${suffix}`);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.message || "Falha ao consultar a API de notícias.");
  }
  return data;
}

export const listarNoticias = (params) => getJson("/noticias", params);
export const obterNoticia = (id) => getJson(`/noticias/${id}`);
export const obterFiltrosNoticias = () => getJson("/noticias/filtros");
export const listarVeiculos = () => getJson("/veiculos");
export const listarNoticiasDoPolitico = (politicoId, params) =>
  getJson(`/politicos/${politicoId}/noticias`, params);
