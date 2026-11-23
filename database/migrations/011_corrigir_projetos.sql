
ALTER TABLE projetos
    ADD COLUMN IF NOT EXISTS sigla_tipo VARCHAR(20),
    ADD COLUMN IF NOT EXISTS id_camara INTEGER,
    ADD COLUMN IF NOT EXISTS atualizado_em TIMESTAMPTZ;

INSERT INTO schema_migrations (version, description)
VALUES (
    '011_corrigir_projetos',
    'Adiciona colunas ausentes à tabela de projetos'
)
ON CONFLICT (version) DO NOTHING;
