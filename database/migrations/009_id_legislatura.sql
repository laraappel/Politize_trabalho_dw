
-- 009_id_legislatura
-- Adiciona o identificador da legislatura à tabela de mandatos.

ALTER TABLE mandatos
    ADD COLUMN IF NOT EXISTS id_legislatura INTEGER;

INSERT INTO schema_migrations (version, description)
VALUES (
    '009_id_legislatura',
    'Adiciona identificador da legislatura à tabela de mandatos'
)
ON CONFLICT (version) DO NOTHING;
