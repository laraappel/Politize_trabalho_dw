-- 010_proposicoes_autores_camara.sql
-- Conserva os autores oficiais das proposições da Câmara em JSONB,
-- sem criar ou substituir registros existentes.

ALTER TABLE proposicoes_camara
    ADD COLUMN IF NOT EXISTS autores_camara JSONB;

CREATE INDEX IF NOT EXISTS ix_proposicoes_camara_autores
    ON proposicoes_camara USING GIN (autores_camara);

INSERT INTO schema_migrations (version, description)
VALUES (
    '010_proposicoes_autores_camara',
    'Relaciona proposicoes da Camara aos seus autores oficiais'
)
ON CONFLICT (version) DO NOTHING;
