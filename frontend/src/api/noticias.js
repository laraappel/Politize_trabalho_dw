import demonstracaoData from './demonstracao.json';

const ROTULOS = {
  fato_documentado: "Fato documentado",
  alegacao: "Alegação",
  opiniao: "Opinião",
  investigacao: "Investigação em andamento",
  nao_classificado: "Sem classificação",
};

const AVISOS = {
  fato_documentado: "Registro confirmado por documento ou ato oficial, conforme revisão editorial.",
  alegacao: "Alegação feita por terceiros. Não é fato comprovado.",
  opiniao: "Texto de opinião ou análise. Expressa o ponto de vista do autor.",
  investigacao: "Investigação ou apuração em curso. Não implica culpa nem condenação.",
  nao_classificado: "A natureza desta notícia ainda não foi classificada.",
};

function slugify(texto) {
  return String(texto || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "") || "sem-nome";
}

function obterListaBruta() {
  if (Array.isArray(demonstracaoData)) return demonstracaoData;
  if (demonstracaoData && Array.isArray(demonstracaoData.noticias)) return demonstracaoData.noticias;
  return [];
}

function normalizarNoticia(n) {
  const naturezaCodigo = n.natureza || "nao_classificado";
  const veiculoNome = n.fonte || n.veiculo?.nome || "Fonte não informada";
  const veiculoSlug = n.veiculo?.slug || slugify(veiculoNome);
  const assuntoNome = n.categoria || n.assunto?.nome || null;
  const assuntoSlug = n.assunto?.slug || (assuntoNome ? slugify(assuntoNome) : null);

  return {
    id: n.id,
    titulo_original: n.titulo_original || n.titulo || "Sem título",
    url_original: n.url_original || "#",
    veiculo: {
      slug: veiculoSlug,
      nome: veiculoNome,
      tipo: n.veiculo?.tipo || "imprensa",
    },
    publicado_em: n.publicado_em || n.data_publicacao || null,
    resumo: n.resumo || null,
    assunto: assuntoSlug ? { slug: assuntoSlug, nome: assuntoNome } : null,
    natureza: {
      codigo: naturezaCodigo,
      rotulo: ROTULOS[naturezaCodigo] || naturezaCodigo,
      aviso: AVISOS[naturezaCodigo] || "",
      origem: n.natureza_origem || "heuristica",
    },
    politicos: Array.isArray(n.politicos)
      ? n.politicos
      : n.politico_id
        ? [
            {
              id: n.politico_id,
              nome: n.politico_nome || `Político ${n.politico_id}`,
              grau_confirmacao: n.grau_confirmacao || "media",
              metodo: n.metodo || "demonstracao",
              origem: "automatica",
            },
          ]
        : [],
    total_atualizacoes: Number(n.total_atualizacoes) || 0,
    atualizacoes: Array.isArray(n.atualizacoes) ? n.atualizacoes : [],
  };
}

function obterLista() {
  return obterListaBruta().map(normalizarNoticia);
}

export async function listarNoticias(params = {}) {
  let lista = obterLista();
  const page = Math.max(1, Number(params.page) || 1);
  const per_page = Math.min(100, Math.max(1, Number(params.per_page) || 10));

  if (params.q) {
    const termo = String(params.q).trim().toLocaleLowerCase("pt-BR");
    if (termo) {
      lista = lista.filter((n) => {
        const texto = [
          n.titulo_original,
          n.resumo,
          n.assunto?.nome,
          n.veiculo?.nome,
          ...n.politicos.map((p) => p.nome),
        ].filter(Boolean).join(" ").toLocaleLowerCase("pt-BR");
        return texto.includes(termo);
      });
    }
  }

  if (params.politico) {
    lista = lista.filter((n) =>
      n.politicos.some((p) => String(p.id) === String(params.politico))
    );
  }
  if (params.veiculo) {
    lista = lista.filter(
      (n) => n.veiculo.slug === params.veiculo || n.veiculo.nome.includes(params.veiculo)
    );
  }
  if (params.assunto) {
    lista = lista.filter(
      (n) =>
        n.assunto &&
        (n.assunto.slug === params.assunto ||
          n.assunto.nome?.toLowerCase() === params.assunto.toLowerCase())
    );
  }
  if (params.natureza) {
    lista = lista.filter((n) => n.natureza.codigo === params.natureza);
  }
  if (params.de) {
    lista = lista.filter((n) => {
      if (!n.publicado_em) return false;
      const data = new Date(n.publicado_em);
      return !Number.isNaN(data.getTime()) && data.toISOString().slice(0, 10) >= params.de;
    });
  }
  if (params.ate) {
    lista = lista.filter((n) => {
      if (!n.publicado_em) return false;
      const data = new Date(n.publicado_em);
      return !Number.isNaN(data.getTime()) && data.toISOString().slice(0, 10) <= params.ate;
    });
  }

  const ordem = params.ordem === "antigas" ? 1 : -1;
  lista = [...lista].sort((a, b) => {
    const da = a.publicado_em ? new Date(a.publicado_em).getTime() : 0;
    const db = b.publicado_em ? new Date(b.publicado_em).getTime() : 0;
    return (da - db) * ordem;
  });

  const total = lista.length;
  const pages = Math.ceil(total / per_page) || 1;
  const paginaValida = Math.min(page, pages);
  const start = (paginaValida - 1) * per_page;
  const items = lista.slice(start, start + per_page);

  return { items, total, page: paginaValida, pages };
}

export async function listarNoticiasDoPolitico(politicoId, params = {}) {
  return listarNoticias({ ...params, politico: String(politicoId) });
}

export async function listarVeiculos() {
  const lista = obterLista();
  const mapa = new Map();
  for (const n of lista) {
    if (!mapa.has(n.veiculo.slug)) {
      mapa.set(n.veiculo.slug, {
        slug: n.veiculo.slug,
        nome: n.veiculo.nome,
        coleta_autorizada: true,
        base_autorizacao: "Portal Oficial de Notícias (demonstração)",
        url_termos: "",
      });
    }
  }
  return { items: [...mapa.values()] };
}

export async function obterFiltrosNoticias() {
  const lista = obterLista();
  const assuntosMap = new Map();
  const veiculosMap = new Map();
  const politicosMap = new Map();

  for (const n of lista) {
    if (n.assunto) assuntosMap.set(n.assunto.slug, n.assunto);
    veiculosMap.set(n.veiculo.slug, { slug: n.veiculo.slug, nome: n.veiculo.nome });
    for (const p of n.politicos) {
      politicosMap.set(p.id, { id: p.id, nome: p.nome });
    }
  }

  return {
    politicos: [...politicosMap.values()],
    veiculos: [...veiculosMap.values()],
    assuntos: [...assuntosMap.values()],
    naturezas: Object.entries(ROTULOS).map(([codigo, rotulo]) => ({ codigo, rotulo })),
  };
}

export async function obterNoticia(id) {
  const lista = obterLista();
  return lista.find((n) => String(n.id) === String(id)) || lista[0] || null;
}

export default {
  listarNoticias,
  listarNoticiasDoPolitico,
  listarVeiculos,
  obterFiltrosNoticias,
  obterNoticia,
};