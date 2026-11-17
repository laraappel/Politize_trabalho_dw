-- 003_dominio: políticos (extensão), mandatos, projetos, votações e despesas.
-- Idempotente. Não recria a tabela politicos (já criada em 002_noticias).

ALTER TABLE politicos ADD COLUMN IF NOT EXISTS slug VARCHAR(80);
ALTER TABLE politicos ADD COLUMN IF NOT EXISTS municipio VARCHAR(120);
ALTER TABLE politicos ADD COLUMN IF NOT EXISTS origem_dados VARCHAR(20) NOT NULL DEFAULT 'demonstracao';
ALTER TABLE politicos ADD COLUMN IF NOT EXISTS fonte_nome VARCHAR(200);
ALTER TABLE politicos ADD COLUMN IF NOT EXISTS fonte_url TEXT;
ALTER TABLE politicos ADD COLUMN IF NOT EXISTS atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE UNIQUE INDEX IF NOT EXISTS uq_politicos_slug
    ON politicos (slug) WHERE slug IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_politicos_nome ON politicos (nome_completo);
CREATE INDEX IF NOT EXISTS ix_politicos_uf_partido ON politicos (uf, partido);

CREATE TABLE IF NOT EXISTS mandatos (
    id              BIGSERIAL PRIMARY KEY,
    politico_id     BIGINT NOT NULL REFERENCES politicos(id) ON DELETE CASCADE,
    cargo           VARCHAR(80) NOT NULL,
    esfera          VARCHAR(20) NOT NULL
        CHECK (esfera IN ('federal', 'estadual', 'municipal')),
    uf              CHAR(2),
    municipio       VARCHAR(120),
    partido         VARCHAR(20),
    legislatura     VARCHAR(40),
    id_legislatura  INTEGER,
    inicio          DATE NOT NULL,
    fim             DATE,
    origem_dados    VARCHAR(20) NOT NULL DEFAULT 'demonstracao'
        CHECK (origem_dados IN ('demonstracao', 'oficial')),
    fonte_nome      VARCHAR(200),
    fonte_url       TEXT,
    atualizado_em   TIMESTAMPTZ,
    UNIQUE (politico_id, cargo, inicio)
);

CREATE INDEX IF NOT EXISTS ix_mandatos_politico ON mandatos (politico_id, inicio DESC);

CREATE TABLE IF NOT EXISTS projetos (
    id                 BIGSERIAL PRIMARY KEY,
    politico_id        BIGINT NOT NULL REFERENCES politicos(id) ON DELETE CASCADE,
    casa               VARCHAR(30) NOT NULL,
    sigla_tipo         VARCHAR(20),
    id_camara          INTEGER,
    numero             INTEGER,
    ano                INTEGER,
    ementa             TEXT,
    situacao           VARCHAR(40),
    data_apresentacao  DATE,
    url_oficial        TEXT,
    origem_dados       VARCHAR(20) NOT NULL DEFAULT 'demonstracao'
        CHECK (origem_dados IN ('demonstracao', 'oficial')),
    fonte_nome         VARCHAR(200),
    fonte_url          TEXT,
    atualizado_em      TIMESTAMPTZ,
    UNIQUE (casa, numero, ano)
);

CREATE INDEX IF NOT EXISTS ix_projetos_politico ON projetos (politico_id, data_apresentacao DESC);

CREATE TABLE IF NOT EXISTS votacoes (
    id                     BIGSERIAL PRIMARY KEY,
    politico_id            BIGINT NOT NULL REFERENCES politicos(id) ON DELETE CASCADE,
    projeto_id             BIGINT REFERENCES projetos(id) ON DELETE SET NULL,
    identificador_externo  VARCHAR(80) NOT NULL,
    casa                   VARCHAR(30) NOT NULL,
    data_votacao           DATE,
    ementa                 TEXT,
    voto                   VARCHAR(20),
    url_oficial            TEXT,
    origem_dados           VARCHAR(20) NOT NULL DEFAULT 'demonstracao'
        CHECK (origem_dados IN ('demonstracao', 'oficial')),
    fonte_nome             VARCHAR(200),
    fonte_url              TEXT,
    UNIQUE (politico_id, identificador_externo)
);

CREATE INDEX IF NOT EXISTS ix_votacoes_politico ON votacoes (politico_id, data_votacao DESC);

CREATE TABLE IF NOT EXISTS despesas (
    id                  BIGSERIAL PRIMARY KEY,
    politico_id         BIGINT NOT NULL REFERENCES politicos(id) ON DELETE CASCADE,
    categoria           VARCHAR(80) NOT NULL,
    descricao           TEXT NOT NULL,
    id_documento_camara VARCHAR(32),
    valor               NUMERIC(14, 2),
    periodo_inicio      DATE NOT NULL,
    periodo_fim         DATE NOT NULL,
    esfera              VARCHAR(20),
    origem_dados        VARCHAR(20) NOT NULL DEFAULT 'demonstracao'
        CHECK (origem_dados IN ('demonstracao', 'oficial')),
    fonte_nome          VARCHAR(200),
    fonte_url           TEXT,
    atualizado_em       TIMESTAMPTZ,
    UNIQUE (politico_id, categoria, periodo_inicio, periodo_fim, descricao)
);

CREATE INDEX IF NOT EXISTS ix_despesas_politico ON despesas (politico_id, periodo_inicio DESC);
CREATE INDEX IF NOT EXISTS ix_despesas_categoria ON despesas (categoria);

INSERT INTO schema_migrations (version, description)
VALUES ('003_dominio', 'Mandatos, projetos, votações, despesas e extensão de políticos')
ON CONFLICT (version) DO NOTHING;
