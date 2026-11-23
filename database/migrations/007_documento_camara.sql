-- 007_documento_camara

ALTER TABLE despesas
    ADD COLUMN IF NOT EXISTS id_documento_camara VARCHAR(32);

INSERT INTO schema_migrations (version, description)
VALUES (
    '007_documento_camara',
    'Adiciona identificador do documento da Câmara às despesas'
)
ON CONFLICT (version) DO NOTHING;