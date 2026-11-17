const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

export class ApiError extends Error {
  constructor(message, { codigo, status } = {}) {
    super(message);
    this.codigo = codigo;
    this.status = status;
  }
}

async function lerResposta(response) {
  try {
    return await response.json();
  } catch {
    if (response.ok) {
      throw new ApiError("A API retornou uma resposta inválida.", { status: response.status });
    }
    return {};
  }
}

export async function apiGet(path, params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") query.set(key, value);
  });
  const suffix = query.toString() ? `?${query}` : "";
  let response;
  try {
    response = await fetch(`${API_URL}/api${path}${suffix}`);
  } catch {
    throw new ApiError("Não foi possível conectar à API.");
  }
  const data = await lerResposta(response);
  if (!response.ok) {
    throw new ApiError(data.message || "Falha ao consultar a API.", {
      codigo: data.error,
      status: response.status,
    });
  }
  return data;
}

export async function getHealth() {
  let response;
  try {
    response = await fetch(`${API_URL}/api/health`);
  } catch {
    throw new ApiError("Não foi possível conectar à API.");
  }
  const data = await lerResposta(response);
  if (!response.ok && response.status !== 503) {
    throw new ApiError(data.message || "Falha ao consultar a API.");
  }
  return data;
}

export { API_URL };
