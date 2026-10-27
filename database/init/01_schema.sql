-- Schema inicial do Voto Transparente.
-- Este arquivo roda apenas na primeira inicialização do volume do PostgreSQL.

CREATE TABLE IF NOT EXISTS schema_migrations (
    id SERIAL PRIMARY KEY,
    version VARCHAR(64) NOT NULL UNIQUE,
    description TEXT,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO schema_migrations (version, description)
VALUES ('001_init', 'Tabela de controle de migrações e base inicial')
ON CONFLICT (version) DO NOTHING;

-- Tabelas de domínio serão adicionadas pelos módulos correspondentes.
-- Convenção: um arquivo por migração, prefixado com número sequencial.
