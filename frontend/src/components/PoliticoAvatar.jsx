import { useEffect, useState } from "react";

function urlOficialDaFoto(politico = {}) {
  const urlsInformadas = [
    politico.foto_url,
    politico.url_foto,
    politico.dados_camara?.ultimoStatus?.urlFoto,
    politico.dados_origem?.foto_url,
  ];

  for (const valor of urlsInformadas) {
    if (!valor) continue;
    try {
      const url = new URL(valor);
      const host = url.hostname.toLowerCase();
      const origemOficial = ["camara.leg.br", "senado.leg.br"].some(
        (dominio) => host === dominio || host.endsWith(`.${dominio}`)
      );
      if (origemOficial) {
        url.protocol = "https:";
        return url.toString();
      }
    } catch {
      // Ignora URLs incompletas e usa a URL oficial derivada do identificador.
    }
  }

  if (politico.id_camara) {
    return `https://www.camara.leg.br/internet/deputado/bandep/${encodeURIComponent(politico.id_camara)}.jpg`;
  }
  if (politico.id_senado) {
    return `https://www.senado.leg.br/senadores/img/fotos-oficiais/senador${encodeURIComponent(politico.id_senado)}.jpg`;
  }
  return "";
}

function iniciais(nome = "") {
  return nome
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((parte) => parte[0].toLocaleUpperCase("pt-BR"))
    .join("") || "VT";
}

function PoliticoAvatar({ politico, tamanho = "card", prioridade = false }) {
  const nome = politico?.nome_exibicao || politico?.nome_urna || politico?.nome_completo || politico?.nome || "Político";
  const url = urlOficialDaFoto(politico);
  const [imagem, setImagem] = useState(url);

  useEffect(() => setImagem(url), [url]);

  return (
    <span className={`politico-avatar politico-avatar--${tamanho}`}>
      {imagem ? (
        <img
          src={imagem}
          alt={`Foto oficial de ${nome}`}
          loading={prioridade ? "eager" : "lazy"}
          decoding="async"
          fetchpriority={prioridade ? "high" : "auto"}
          width={tamanho === "perfil" ? 160 : 96}
          height={tamanho === "perfil" ? 160 : 96}
          onError={() => setImagem("")}
        />
      ) : (
        <span className="politico-avatar-fallback" role="img" aria-label={`Foto indisponível para ${nome}`}>
          <svg viewBox="0 0 64 64" aria-hidden="true">
            <circle cx="32" cy="23" r="12" />
            <path d="M10 58c1-13 9-21 22-21s21 8 22 21" />
          </svg>
          <span aria-hidden="true">{iniciais(nome)}</span>
        </span>
      )}
    </span>
  );
}

export default PoliticoAvatar;
