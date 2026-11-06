-- 004_integridade_dados: valida origem oficial, períodos e identificadores.
-- Aplicada uma vez pelo comando `flask --app wsgi migrate`.

ALTER TABLE politicos
    ADD CONSTRAINT ck_politicos_origem_dados
        CHECK (origem_dados IN ('demonstracao', 'oficial')),
    ADD CONSTRAINT ck_politicos_fonte_oficial
        CHECK (
            origem_dados <> 'oficial'
            OR (
                fonte_nome IS NOT NULL
                AND BTRIM(fonte_nome) <> ''
                AND fonte_url IS NOT NULL
                AND fonte_url ~* '^https?://[^[:space:]/]+'
            )
        );

ALTER TABLE mandatos
    ADD CONSTRAINT ck_mandatos_periodo
        CHECK (fim IS NULL OR fim >= inicio),
    ADD CONSTRAINT ck_mandatos_fonte_oficial
        CHECK (
            origem_dados <> 'oficial'
            OR (
                fonte_nome IS NOT NULL
                AND BTRIM(fonte_nome) <> ''
                AND fonte_url IS NOT NULL
                AND fonte_url ~* '^https?://[^[:space:]/]+'
            )
        );

ALTER TABLE projetos
    ADD CONSTRAINT ck_projetos_identificadores
        CHECK (ano IS NOT NULL AND ano >= 1823 AND numero IS NOT NULL AND numero > 0),
    ADD CONSTRAINT ck_projetos_fonte_oficial
        CHECK (
            origem_dados <> 'oficial'
            OR (
                fonte_nome IS NOT NULL
                AND BTRIM(fonte_nome) <> ''
                AND fonte_url IS NOT NULL
                AND fonte_url ~* '^https?://[^[:space:]/]+'
            )
        );

ALTER TABLE votacoes
    ADD CONSTRAINT ck_votacoes_voto
        CHECK (voto IS NULL OR voto IN ('sim', 'nao', 'abstencao', 'obstrucao', 'ausente', 'nao_informado')),
    ADD CONSTRAINT ck_votacoes_fonte_oficial
        CHECK (
            origem_dados <> 'oficial'
            OR (
                fonte_nome IS NOT NULL
                AND BTRIM(fonte_nome) <> ''
                AND fonte_url IS NOT NULL
                AND fonte_url ~* '^https?://[^[:space:]/]+'
            )
        );

ALTER TABLE despesas
    ADD CONSTRAINT ck_despesas_periodo
        CHECK (periodo_fim >= periodo_inicio),
    ADD CONSTRAINT ck_despesas_fonte_oficial
        CHECK (
            origem_dados <> 'oficial'
            OR (
                fonte_nome IS NOT NULL
                AND BTRIM(fonte_nome) <> ''
                AND fonte_url IS NOT NULL
                AND fonte_url ~* '^https?://[^[:space:]/]+'
            )
        );

INSERT INTO schema_migrations (version, description)
VALUES ('004_integridade_dados', 'Valida proveniência oficial e consistência de períodos e identificadores')
ON CONFLICT (version) DO NOTHING;
