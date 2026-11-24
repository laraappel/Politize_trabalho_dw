import { apiGet } from "./client";

export const listarCargosEletivos = (params) => apiGet("/cargos-eletivos", params);
export const obterFiltrosCargosEletivos = () => apiGet("/cargos-eletivos/filtros");
export const listarCandidaturasPolitico = (id, params) => apiGet(`/politicos/${id}/candidaturas`, params);
