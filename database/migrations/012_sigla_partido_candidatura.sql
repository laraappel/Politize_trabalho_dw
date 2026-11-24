-- Guarda a sigla eleitoral como publicada para cada candidatura, sem presumir IDs partidários.
ALTER TABLE candidaturas
    ADD COLUMN IF NOT EXISTS sigla_partido VARCHAR(32);

INSERT INTO schema_migrations (version, description)
VALUES (
    '012_sigla_partido_candidatura',
    'Preserva a sigla partidaria publicada na candidatura eleitoral'
)
ON CONFLICT (version) DO NOTHING;
