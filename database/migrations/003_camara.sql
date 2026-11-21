-- 003_camara: integração com a API oficial de Dados Abertos da Câmara.
-- Não cria uma segunda tabela de políticos: complementa `politicos`, já usada
-- pelo módulo de notícias, preservando os IDs locais e o id_camara oficial.

ALTER TABLE politicos ADD COLUMN IF NOT EXISTS origem_dados VARCHAR(80) DEFAULT 'demonstracao';
ALTER TABLE politicos ADD COLUMN IF NOT EXISTS coletado_em TIMESTAMPTZ;
ALTER TABLE politicos ADD COLUMN IF NOT EXISTS atualizado_em TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE politicos ADD COLUMN IF NOT EXISTS dados_camara JSONB;
CREATE UNIQUE INDEX IF NOT EXISTS uq_politicos_id_camara
    ON politicos (id_camara) WHERE id_camara IS NOT NULL;

CREATE TABLE IF NOT EXISTS partidos_camara (
    id BIGSERIAL PRIMARY KEY,
    sigla VARCHAR(30) NOT NULL UNIQUE,
    id_partido_camara INTEGER UNIQUE,
    nome VARCHAR(180),
    uri_origem TEXT,
    origem VARCHAR(80) NOT NULL DEFAULT 'camara_deputados',
    coletado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    dados_origem JSONB
);

CREATE TABLE IF NOT EXISTS mandatos_camara (
    id BIGSERIAL PRIMARY KEY,
    politico_id BIGINT NOT NULL REFERENCES politicos(id) ON DELETE CASCADE,
    id_deputado_camara INTEGER NOT NULL,
    id_legislatura INTEGER,
    chave_origem VARCHAR(180) NOT NULL UNIQUE,
    data_inicio DATE,
    data_fim DATE,
    partido_sigla VARCHAR(30),
    uf CHAR(2),
    situacao TEXT,
    origem VARCHAR(80) NOT NULL DEFAULT 'camara_deputados',
    coletado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    dados_origem JSONB
);
CREATE INDEX IF NOT EXISTS ix_mandatos_camara_politico
    ON mandatos_camara (id_deputado_camara, id_legislatura);

CREATE TABLE IF NOT EXISTS despesas_camara (
    id BIGSERIAL PRIMARY KEY,
    id_deputado_camara INTEGER NOT NULL,
    id_documento BIGINT,
    chave_origem VARCHAR(180) NOT NULL UNIQUE,
    ano INTEGER,
    mes INTEGER,
    tipo_despesa TEXT,
    tipo_documento TEXT,
    data_documento DATE,
    fornecedor TEXT,
    cnpj_cpf_fornecedor VARCHAR(30),
    valor_documento NUMERIC(14,2),
    valor_liquido NUMERIC(14,2),
    url_documento TEXT,
    origem VARCHAR(80) NOT NULL DEFAULT 'camara_deputados',
    coletado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    dados_origem JSONB
);
CREATE INDEX IF NOT EXISTS ix_despesas_camara_deputado_periodo
    ON despesas_camara (id_deputado_camara, ano, mes);
CREATE INDEX IF NOT EXISTS ix_despesas_camara_tipo
    ON despesas_camara (tipo_despesa, ano, mes);

CREATE TABLE IF NOT EXISTS proposicoes_camara (
    id BIGSERIAL PRIMARY KEY,
    id_proposicao_camara INTEGER NOT NULL UNIQUE,
    uri_origem TEXT,
    sigla_tipo VARCHAR(30),
    numero INTEGER,
    ano INTEGER,
    ementa TEXT,
    data_apresentacao DATE,
    uri_orgao_numerador TEXT,
    status_descricao TEXT,
    status_data_hora TIMESTAMPTZ,
    origem VARCHAR(80) NOT NULL DEFAULT 'camara_deputados',
    coletado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    dados_origem JSONB
);
CREATE INDEX IF NOT EXISTS ix_proposicoes_camara_ano_tipo
    ON proposicoes_camara (ano, sigla_tipo);

CREATE TABLE IF NOT EXISTS data_sync_logs (
    id BIGSERIAL PRIMARY KEY,
    fonte VARCHAR(80) NOT NULL,
    entidade VARCHAR(80) NOT NULL,
    operacao VARCHAR(30) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('em_andamento','ok','sem_alteracao','erro')),
    iniciada_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finalizada_em TIMESTAMPTZ,
    registros_lidos INTEGER NOT NULL DEFAULT 0,
    registros_novos INTEGER NOT NULL DEFAULT 0,
    registros_atualizados INTEGER NOT NULL DEFAULT 0,
    mensagem TEXT
);
CREATE INDEX IF NOT EXISTS ix_data_sync_logs_fonte_inicio
    ON data_sync_logs (fonte, iniciada_em DESC);

INSERT INTO schema_migrations (version, description)
VALUES ('003_camara', 'Integração com dados abertos da Câmara dos Deputados')
ON CONFLICT (version) DO NOTHING;
