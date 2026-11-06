-- 002_noticias: módulo de notícias políticas (apenas metadados e referências).
-- Idempotente: pode ser reaplicado sem efeito colateral.
-- Aplicação: `docker compose exec backend flask --app wsgi migrate`

-- ---------------------------------------------------------------------------
-- DEPENDÊNCIA: cadastro compartilhado de políticos.
-- Cria a base mínima quando necessário; 003_dominio.sql a estende com campos
-- usados pelo módulo ativo de políticos.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS politicos (
    id            BIGSERIAL PRIMARY KEY,
    nome_completo VARCHAR(200) NOT NULL,
    nome_urna     VARCHAR(200),
    apelidos      TEXT[] NOT NULL DEFAULT '{}',
    cargo         VARCHAR(80),
    uf            CHAR(2),
    partido       VARCHAR(20),
    id_camara     INTEGER UNIQUE,
    id_senado     INTEGER UNIQUE,
    criado_em     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- Veículos (fontes) e a base de autorização de cada um.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS veiculos (
    id                  SERIAL PRIMARY KEY,
    slug                VARCHAR(60) NOT NULL UNIQUE,
    nome                VARCHAR(120) NOT NULL,
    dominio             VARCHAR(120) NOT NULL,
    tipo                VARCHAR(30) NOT NULL DEFAULT 'imprensa'
        CHECK (tipo IN ('imprensa', 'agencia_publica', 'agencia_institucional')),
    coleta_autorizada   BOOLEAN NOT NULL DEFAULT FALSE,
    permite_resumo      BOOLEAN NOT NULL DEFAULT FALSE,
    base_autorizacao    TEXT NOT NULL,
    url_termos          TEXT,
    ultima_coleta_em    TIMESTAMPTZ,
    criado_em           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- Notícias: somente referência (título original, link, resumo curto).
-- Nunca armazenamos o corpo da matéria.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS noticias (
    id               BIGSERIAL PRIMARY KEY,
    veiculo_id       INTEGER NOT NULL REFERENCES veiculos(id),
    url_original     TEXT NOT NULL,
    url_canonica     TEXT NOT NULL UNIQUE,
    guid_origem      TEXT,
    chave_dedup      CHAR(64) NOT NULL UNIQUE,
    titulo_original  TEXT NOT NULL,
    resumo           VARCHAR(400),
    publicado_em     TIMESTAMPTZ,
    assunto_slug     VARCHAR(80),
    assunto_nome     VARCHAR(120),
    natureza         VARCHAR(30) NOT NULL DEFAULT 'nao_classificado'
        CHECK (natureza IN ('fato_documentado', 'alegacao', 'opiniao',
                            'investigacao', 'nao_classificado')),
    natureza_origem  VARCHAR(20) NOT NULL DEFAULT 'heuristica'
        CHECK (natureza_origem IN ('heuristica', 'editorial')),
    coletado_em      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_noticias_veiculo_guid
    ON noticias (veiculo_id, guid_origem) WHERE guid_origem IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_noticias_publicado_em ON noticias (publicado_em DESC, id DESC);
CREATE INDEX IF NOT EXISTS ix_noticias_veiculo ON noticias (veiculo_id);
CREATE INDEX IF NOT EXISTS ix_noticias_assunto ON noticias (assunto_slug);

-- ---------------------------------------------------------------------------
-- Associação notícia <-> político, com a evidência e o grau de confirmação.
-- Só associações 'confirmada' aparecem publicamente.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS noticia_politicos (
    noticia_id        BIGINT NOT NULL REFERENCES noticias(id) ON DELETE CASCADE,
    politico_id       BIGINT NOT NULL REFERENCES politicos(id) ON DELETE CASCADE,
    status            VARCHAR(20) NOT NULL
        CHECK (status IN ('confirmada', 'pendente_revisao', 'rejeitada')),
    grau_confirmacao  VARCHAR(10) NOT NULL
        CHECK (grau_confirmacao IN ('alta', 'media', 'baixa', 'manual')),
    metodo            VARCHAR(40) NOT NULL,
    origem            VARCHAR(12) NOT NULL DEFAULT 'automatica'
        CHECK (origem IN ('automatica', 'manual')),
    evidencias        JSONB NOT NULL DEFAULT '[]'::jsonb,
    revisado_por      VARCHAR(80),
    revisado_em       TIMESTAMPTZ,
    criado_em         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (noticia_id, politico_id)
);

CREATE INDEX IF NOT EXISTS ix_noticia_politicos_politico
    ON noticia_politicos (politico_id, status);

-- ---------------------------------------------------------------------------
-- Desdobramentos, correções e complementos de um registro.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS noticia_atualizacoes (
    id                      BIGSERIAL PRIMARY KEY,
    noticia_id              BIGINT NOT NULL REFERENCES noticias(id) ON DELETE CASCADE,
    tipo                    VARCHAR(30) NOT NULL
        CHECK (tipo IN ('desdobramento', 'correcao', 'complemento', 'alteracao_titulo')),
    descricao               TEXT NOT NULL,
    url_referencia          TEXT,
    noticia_relacionada_id  BIGINT REFERENCES noticias(id) ON DELETE SET NULL,
    criado_por              VARCHAR(80) NOT NULL DEFAULT 'sistema',
    criado_em               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_noticia_atualizacoes_noticia
    ON noticia_atualizacoes (noticia_id, criado_em);

-- ---------------------------------------------------------------------------
-- Auditoria das coletas.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS coletas_noticias (
    id                 BIGSERIAL PRIMARY KEY,
    veiculo_id         INTEGER NOT NULL REFERENCES veiculos(id),
    iniciada_em        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finalizada_em      TIMESTAMPTZ,
    status             VARCHAR(20) NOT NULL DEFAULT 'em_andamento'
        CHECK (status IN ('em_andamento', 'ok', 'sem_alteracao', 'erro', 'ignorada')),
    itens_lidos        INTEGER NOT NULL DEFAULT 0,
    itens_novos        INTEGER NOT NULL DEFAULT 0,
    itens_atualizados  INTEGER NOT NULL DEFAULT 0,
    itens_descartados  INTEGER NOT NULL DEFAULT 0,
    mensagem           TEXT
);

INSERT INTO schema_migrations (version, description)
VALUES ('002_noticias', 'Módulo de notícias: veículos, notícias, associações, atualizações, coletas')
ON CONFLICT (version) DO NOTHING;
