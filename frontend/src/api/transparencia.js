import { apiGet } from "./client";

export const obterPanorama = () => apiGet("/transparencia");
export const listarDespesas = (params) => apiGet("/transparencia/despesas", params);
export const obterFiltrosTransparencia = () => apiGet("/transparencia/filtros");
