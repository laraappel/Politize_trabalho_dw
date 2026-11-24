-- 009_dominios_eleitorais_transparencia.sql
-- Completa os domínios eleitorais e de transparência sem alterar registros existentes.

CREATE TABLE IF NOT EXISTS partidos (
    id BIGSERIAL PRIMARY KEY,
    id_camara INTEGER NOT NULL UNIQUE,
    sigla VARCHAR(30) NOT NULL,
    nome VARCHAR(200) NOT NULL,
    uri TEXT,
    origem_dados VARCHAR(20) NOT NULL DEFAULT 'oficial'
        CHECK (origem_dados IN ('demonstracao', 'oficial')),
    fonte_nome VARCHAR(200) NOT NULL,
    fonte_url TEXT NOT NULL,
    coletado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_partidos_id_camara ON partidos(id_camara);
CREATE INDEX IF NOT EXISTS ix_partidos_sigla ON partidos(sigla);

CREATE TABLE IF NOT EXISTS candidaturas (
    id BIGSERIAL PRIMARY KEY,
    politico_id BIGINT NOT NULL REFERENCES politicos(id) ON DELETE CASCADE,
    partido_id BIGINT REFERENCES partidos(id) ON DELETE RESTRICT,
    ano INTEGER NOT NULL CHECK (ano >= 1890),
    cargo VARCHAR(64) NOT NULL,
    uf CHAR(2),
    municipio VARCHAR(120),
    nome_urna VARCHAR(200),
    numero_candidatura VARCHAR(16),
    resultado VARCHAR(32),
    votos INTEGER CHECK (votos IS NULL OR votos >= 0),
    origem_dados VARCHAR(20) NOT NULL DEFAULT 'demonstracao'
        CHECK (origem_dados IN ('demonstracao', 'oficial')),
    fonte_nome VARCHAR(200),
    fonte_url TEXT,
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (politico_id, ano, cargo, uf, municipio)
);

CREATE INDEX IF NOT EXISTS ix_candidaturas_ano ON candidaturas (ano DESC);
CREATE INDEX IF NOT EXISTS ix_candidaturas_politico ON candidaturas (politico_id);
CREATE INDEX IF NOT EXISTS ix_candidaturas_partido ON candidaturas (partido_id);
CREATE INDEX IF NOT EXISTS ix_candidaturas_resultado ON candidaturas (resultado);

CREATE TABLE IF NOT EXISTS propostas_campanha (
    id BIGSERIAL PRIMARY KEY,
    candidatura_id BIGINT NOT NULL REFERENCES candidaturas(id) ON DELETE CASCADE,
    titulo VARCHAR(255) NOT NULL,
    descricao TEXT,
    tema VARCHAR(64),
    origem_dados VARCHAR(20) NOT NULL DEFAULT 'demonstracao'
        CHECK (origem_dados IN ('demonstracao', 'oficial')),
    fonte_nome VARCHAR(200),
    fonte_url TEXT,
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (candidatura_id, titulo)
);

CREATE INDEX IF NOT EXISTS ix_propostas_campanha_candidatura
    ON propostas_campanha (candidatura_id);
CREATE INDEX IF NOT EXISTS ix_propostas_campanha_tema
    ON propostas_campanha (tema);

CREATE TABLE IF NOT EXISTS projeto_coautorias (
    id BIGSERIAL PRIMARY KEY,
    projeto_id BIGINT NOT NULL REFERENCES projetos(id) ON DELETE CASCADE,
    politico_id BIGINT NOT NULL REFERENCES politicos(id) ON DELETE CASCADE,
    papel VARCHAR(16) NOT NULL DEFAULT 'coautor'
        CHECK (papel IN ('autor', 'coautor', 'relator')),
    origem_dados VARCHAR(20) NOT NULL DEFAULT 'demonstracao'
        CHECK (origem_dados IN ('demonstracao', 'oficial')),
    fonte_nome VARCHAR(200),
    fonte_url TEXT,
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (projeto_id, politico_id)
);

CREATE INDEX IF NOT EXISTS ix_projeto_coautorias_projeto
    ON projeto_coautorias (projeto_id);
CREATE INDEX IF NOT EXISTS ix_projeto_coautorias_politico
    ON projeto_coautorias (politico_id);

CREATE TABLE IF NOT EXISTS remuneracoes (
    id BIGSERIAL PRIMARY KEY,
    politico_id BIGINT NOT NULL REFERENCES politicos(id) ON DELETE CASCADE,
    cargo VARCHAR(120),
    periodo_inicio DATE NOT NULL,
    periodo_fim DATE NOT NULL,
    valor_bruto NUMERIC(14, 2),
    beneficios NUMERIC(14, 2),
    descontos NUMERIC(14, 2),
    valor_liquido NUMERIC(14, 2),
    origem_dados VARCHAR(20) NOT NULL DEFAULT 'demonstracao'
        CHECK (origem_dados IN ('demonstracao', 'oficial')),
    fonte_nome VARCHAR(200),
    fonte_url TEXT,
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (periodo_fim >= periodo_inicio),
    CHECK (
        (valor_bruto IS NULL OR valor_bruto >= 0)
        AND (beneficios IS NULL OR beneficios >= 0)
        AND (descontos IS NULL OR descontos >= 0)
        AND (valor_liquido IS NULL OR valor_liquido >= 0)
    ),
    UNIQUE (politico_id, cargo, periodo_inicio, periodo_fim)
);

CREATE INDEX IF NOT EXISTS ix_remuneracoes_politico_periodo
    ON remuneracoes (politico_id, periodo_inicio DESC);

CREATE TABLE IF NOT EXISTS patrimonio_declarado (
    id BIGSERIAL PRIMARY KEY,
    politico_id BIGINT NOT NULL REFERENCES politicos(id) ON DELETE CASCADE,
    candidatura_id BIGINT REFERENCES candidaturas(id) ON DELETE SET NULL,
    ano_referencia INTEGER NOT NULL CHECK (ano_referencia >= 1985),
    tipo VARCHAR(80) NOT NULL,
    descricao TEXT,
    valor NUMERIC(14, 2),
    localizacao VARCHAR(255),
    origem_dados VARCHAR(20) NOT NULL DEFAULT 'demonstracao'
        CHECK (origem_dados IN ('demonstracao', 'oficial')),
    fonte_nome VARCHAR(200),
    fonte_url TEXT,
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (valor IS NULL OR valor >= 0)
);

CREATE INDEX IF NOT EXISTS ix_patrimonio_politico_ano
    ON patrimonio_declarado (politico_id, ano_referencia DESC);
CREATE INDEX IF NOT EXISTS ix_patrimonio_candidatura
    ON patrimonio_declarado (candidatura_id);

INSERT INTO schema_migrations (version, description)
VALUES (
    '009_dominios_eleitorais_transparencia',
    'Adiciona candidaturas, propostas de campanha, coautorias, remuneracoes e patrimonio declarado'
)
ON CONFLICT (version) DO NOTHING;
