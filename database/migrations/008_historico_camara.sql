-- 008_historico_camara.sql
-- Separa eventos hist?ricos de per?odos de mandato.
-- N?o altera nem remove registros antigos de mandatos_camara.

CREATE TABLE IF NOT EXISTS historicos_camara (
    id BIGSERIAL PRIMARY KEY,
    politico_id BIGINT NOT NULL
        REFERENCES politicos(id) ON DELETE CASCADE,
    id_deputado_camara INTEGER NOT NULL,
    id_legislatura INTEGER,
    chave_origem VARCHAR(180) NOT NULL UNIQUE,
    nome TEXT,
    nome_eleitoral TEXT,
    sigla_partido VARCHAR(30),
    sigla_uf VARCHAR(2),
    email TEXT,
    url_foto TEXT,
    data_hora TIMESTAMPTZ,
    situacao TEXT,
    condicao_eleitoral TEXT,
    descricao_status TEXT,
    uri_origem TEXT,
    origem VARCHAR(80) NOT NULL DEFAULT 'camara_deputados',
    coletado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    dados_origem JSONB
);

CREATE INDEX IF NOT EXISTS ix_historicos_camara_deputado_data
    ON historicos_camara (id_deputado_camara, data_hora DESC);

INSERT INTO schema_migrations (version, description)
VALUES (
    '008_historico_camara',
    'Separa eventos historicos da Camara dos periodos de mandato'
)
ON CONFLICT (version) DO NOTHING;
