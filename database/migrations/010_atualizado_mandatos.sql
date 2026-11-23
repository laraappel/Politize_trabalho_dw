
-- 010_atualizado_mandatos
-- Adiciona a data de atualização dos mandatos.

ALTER TABLE mandatos
    ADD COLUMN IF NOT EXISTS atualizado_em TIMESTAMPTZ;

INSERT INTO schema_migrations (version, description)
VALUES (
    '010_atualizado_mandatos',
    'Adiciona data de atualização à tabela de mandatos'
)
ON CONFLICT (version) DO NOTHING;
