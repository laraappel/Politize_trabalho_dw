export function formatarData(iso) {
  if (!iso) return null;
  const data = new Date(iso.length <= 10 ? `${iso}T12:00:00` : iso);
  if (Number.isNaN(data.getTime())) return null;
  return data.toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "long",
    year: "numeric",
    timeZone: "America/Sao_Paulo",
  });
}

export function formatarDinheiro(valor) {
  if (valor === null || valor === undefined || valor === "") return null;
  const numero = Number(valor);
  if (Number.isNaN(numero)) return null;
  return numero.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function rotuloVoto(voto) {
  if (!voto) return null;
  const mapa = {
    sim: "Sim",
    nao: "Não",
    abstencao: "Abstenção",
    obstrucao: "Obstrução",
    ausente: "Ausente",
    nao_informado: "Não informado",
  };
  return mapa[voto] || voto;
}
