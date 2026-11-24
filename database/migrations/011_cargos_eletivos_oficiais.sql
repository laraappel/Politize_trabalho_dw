-- 011_cargos_eletivos_oficiais.sql
-- Cadastro público verificável de cargos eletivos sem inventar ocupantes.

CREATE TABLE IF NOT EXISTS cargos_eletivos (
    id BIGSERIAL PRIMARY KEY,
    politico_id BIGINT REFERENCES politicos(id) ON DELETE CASCADE,
    cargo VARCHAR(64) NOT NULL,
    esfera VARCHAR(20) NOT NULL CHECK (esfera IN ('federal', 'estadual', 'municipal')),
    uf CHAR(2),
    municipio VARCHAR(120),
    partido VARCHAR(32),
    ano_eleicao INTEGER,
    ano_inicio INTEGER,
    ano_fim INTEGER,
    situacao VARCHAR(64) NOT NULL DEFAULT 'em_exercicio',
    identificador_externo VARCHAR(128),
    origem VARCHAR(80) NOT NULL,
    fonte_nome VARCHAR(200) NOT NULL,
    fonte_url TEXT NOT NULL,
    dados_origem JSONB,
    coletado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (origem, identificador_externo)
);

CREATE INDEX IF NOT EXISTS ix_cargos_eletivos_cargo_esfera
    ON cargos_eletivos (cargo, esfera);
CREATE INDEX IF NOT EXISTS ix_cargos_eletivos_uf_municipio
    ON cargos_eletivos (uf, municipio);
CREATE INDEX IF NOT EXISTS ix_cargos_eletivos_politico
    ON cargos_eletivos (politico_id);
CREATE INDEX IF NOT EXISTS ix_cargos_eletivos_situacao
    ON cargos_eletivos (situacao);

INSERT INTO schema_migrations (version, description)
VALUES (
    '011_cargos_eletivos_oficiais',
    'Cargos eletivos oficiais com proveniencia e cobertura verificavel'
)
ON CONFLICT (version) DO NOTHING;
