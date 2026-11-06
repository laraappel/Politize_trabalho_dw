import { apiGet } from "./client";

export const listarNoticias = (params) => apiGet("/noticias", params);
export const obterNoticia = (id) => apiGet(`/noticias/${id}`);
export const obterFiltrosNoticias = () => apiGet("/noticias/filtros");
export const listarVeiculos = () => apiGet("/veiculos");
export const listarNoticiasDoPolitico = (politicoId, params) =>
  apiGet(`/politicos/${politicoId}/noticias`, params);
