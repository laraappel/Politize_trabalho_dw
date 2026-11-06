import { apiGet } from "./client";

export const listarPoliticos = (params) => apiGet("/politicos", params);
export const obterFiltrosPoliticos = () => apiGet("/politicos/filtros");
export const obterPolitico = (id) => apiGet(`/politicos/${id}`);
export const listarMandatos = (id, params) => apiGet(`/politicos/${id}/mandatos`, params);
export const listarProjetos = (id, params) => apiGet(`/politicos/${id}/projetos`, params);
export const listarVotacoes = (id, params) => apiGet(`/politicos/${id}/votacoes`, params);
export const listarDespesasDoPolitico = (id, params) => apiGet(`/politicos/${id}/despesas`, params);
