-- 005_data_sources: cadastro de fontes e logs genéricos de sincronização.
-- A tabela data_sync_logs permanece exclusiva da integração com a Câmara.

CREATE TABLE IF NOT EXISTS data_sources (
    id SERIAL PRIMARY KEY,
    code VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    url VARCHAR(500),
    description TEXT,
    is_official BOOLEAN NOT NULL DEFAULT FALSE,
    is_demo BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_data_sources_is_official
    ON data_sources (is_official);
CREATE INDEX IF NOT EXISTS ix_data_sources_is_demo
    ON data_sources (is_demo);

CREATE TABLE IF NOT EXISTS data_source_sync_logs (
    id SERIAL PRIMARY KEY,
    data_source_id INTEGER NOT NULL
        REFERENCES data_sources(id) ON DELETE RESTRICT,
    entity_name VARCHAR(64) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    status VARCHAR(16) NOT NULL
        CHECK (status IN ('running', 'success', 'failed')),
    records_read INTEGER NOT NULL DEFAULT 0,
    records_upserted INTEGER NOT NULL DEFAULT 0,
    records_failed INTEGER NOT NULL DEFAULT 0,
    message TEXT,
    CONSTRAINT ck_data_source_sync_logs_counts
        CHECK (
            records_read >= 0
            AND records_upserted >= 0
            AND records_failed >= 0
        )
);

CREATE INDEX IF NOT EXISTS ix_data_source_sync_logs_source_started
    ON data_source_sync_logs (data_source_id, started_at);
CREATE INDEX IF NOT EXISTS ix_data_source_sync_logs_status
    ON data_source_sync_logs (status);

INSERT INTO schema_migrations (version, description)
VALUES ('005_data_sources', 'Fontes de dados e logs genéricos de sincronização')
ON CONFLICT (version) DO NOTHING;
