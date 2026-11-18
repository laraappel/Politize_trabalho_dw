-- 006_fontes_dados: cadastro genérico de fontes e o log separado da Câmara.
-- data_sync_logs continua sendo o log da Câmara (003_camara.sql).
-- data_source_sync_logs registra sincronizações ligadas a data_sources.
-- partidos corresponde ao modelo Partido; a Câmara ativa usa partidos_camara.

CREATE TABLE IF NOT EXISTS data_sources (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(64) NOT NULL UNIQUE,
    name        VARCHAR(255) NOT NULL,
    url         VARCHAR(500),
    description TEXT,
    is_official BOOLEAN NOT NULL DEFAULT FALSE,
    is_demo     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_data_sources_is_official ON data_sources (is_official);
CREATE INDEX IF NOT EXISTS ix_data_sources_is_demo ON data_sources (is_demo);

CREATE TABLE IF NOT EXISTS data_source_sync_logs (
    id                SERIAL PRIMARY KEY,
    data_source_id    INTEGER NOT NULL REFERENCES data_sources(id) ON DELETE RESTRICT,
    entity_name       VARCHAR(64) NOT NULL,
    started_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at       TIMESTAMPTZ,
    status            VARCHAR(16) NOT NULL,
    records_read      INTEGER NOT NULL DEFAULT 0,
    records_upserted  INTEGER NOT NULL DEFAULT 0,
    records_failed    INTEGER NOT NULL DEFAULT 0,
    message           TEXT,
    CONSTRAINT ck_data_source_sync_logs_status
        CHECK (status IN ('running', 'success', 'failed')),
    CONSTRAINT ck_data_source_sync_logs_counts
        CHECK (records_read >= 0 AND records_upserted >= 0 AND records_failed >= 0)
);

CREATE INDEX IF NOT EXISTS ix_data_source_sync_logs_source_started
    ON data_source_sync_logs (data_source_id, started_at);
CREATE INDEX IF NOT EXISTS ix_data_source_sync_logs_status
    ON data_source_sync_logs (status);

CREATE TABLE IF NOT EXISTS partidos (
    id            BIGSERIAL PRIMARY KEY,
    id_camara     INTEGER NOT NULL UNIQUE,
    sigla         VARCHAR(30) NOT NULL,
    nome          VARCHAR(200) NOT NULL,
    uri           TEXT,
    origem_dados  VARCHAR(20) NOT NULL DEFAULT 'oficial',
    fonte_nome    VARCHAR(200) NOT NULL,
    fonte_url     TEXT NOT NULL,
    coletado_em   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO schema_migrations (version, description)
VALUES (
    '006_fontes_dados',
    'Cria data_sources, data_source_sync_logs e partidos'
)
ON CONFLICT (version) DO NOTHING;
