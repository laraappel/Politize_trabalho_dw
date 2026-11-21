-- 007_corrige_identificador_despesa_camara.sql
-- Preserva os registros existentes e corrige o tipo do identificador oficial.

ALTER TABLE despesas_camara
    ALTER COLUMN id_documento TYPE TEXT
    USING id_documento::TEXT;

UPDATE despesas_camara
SET id_documento = NULLIF(dados_origem->>'codDocumento', '')
WHERE dados_origem IS NOT NULL
  AND dados_origem ? 'codDocumento';

INSERT INTO schema_migrations (version, description)
VALUES (
    '007_corrige_identificador_despesa_camara',
    'Corrige o identificador das despesas da Camara para TEXT e importa codDocumento'
)
ON CONFLICT (version) DO NOTHING;
