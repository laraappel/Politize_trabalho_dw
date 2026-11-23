
-- 008_atualizado_despesas: adiciona data de atualização das despesas.

ALTER TABLE despesas
    ADD COLUMN IF NOT EXISTS atualizado_em TIMESTAMPTZ;

INSERT INTO schema_migrations (version, description)
VALUES (
    '008_atualizado_despesas',
    'Adiciona data de atualização às despesas'
)
ON CONFLICT (version) DO NOTHING;
