import { apiGet } from "./client";

export const listarDeputadosCamara = (params) => apiGet("/deputados", params);
export const obterDeputadoCamara = (idCamara) => apiGet(`/deputados/${idCamara}`);
export const listarDespesasDeputadoCamara = (idCamara, params) => apiGet(`/deputados/${idCamara}/despesas`, params);
export const listarProposicoesCamara = (params) => apiGet("/proposicoes", params);
export const listarPartidosCamara = () => apiGet("/partidos");
export const listarLogsCamara = (params) => apiGet("/data-sync-logs", params);
