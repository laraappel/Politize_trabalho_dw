const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

export async function getHealth() {
  const response = await fetch(`${API_URL}/api/health`);
  const data = await response.json();

  if (!response.ok && response.status !== 503) {
    throw new Error(data.message || "Falha ao consultar a API.");
  }

  return data;
}

export { API_URL };
