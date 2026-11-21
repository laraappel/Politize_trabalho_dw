-- 006_atualizacao_modelos.sql
-- Completa as colunas dos modelos atuais sem apagar dados existentes.

ALTER TABLE despesas
    ADD COLUMN IF NOT EXISTS id_documento_camara VARCHAR(32),
    ADD COLUMN IF NOT EXISTS atualizado_em TIMESTAMPTZ;

ALTER TABLE despesas
    ALTER COLUMN categoria TYPE VARCHAR(160);

ALTER TABLE mandatos
    ADD COLUMN IF NOT EXISTS id_legislatura INTEGER,
    ADD COLUMN IF NOT EXISTS atualizado_em TIMESTAMPTZ;

ALTER TABLE projetos
    ADD COLUMN IF NOT EXISTS sigla_tipo VARCHAR(20),
    ADD COLUMN IF NOT EXISTS id_camara INTEGER,
    ADD COLUMN IF NOT EXISTS atualizado_em TIMESTAMPTZ;
INSERT INTO schema_migrations (version, description)
VALUES (
    '006_atualizacao_modelos',
    'Completa as colunas dos modelos atuais sem apagar dados existentes'
)
ON CONFLICT (version) DO NOTHING;
