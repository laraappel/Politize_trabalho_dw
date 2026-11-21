-- 005_reconciliar_politicos: alinha politicos entre o domínio e a Câmara.
-- Idempotente. Roda depois de 003_dominio, 003_camara e 004_integridade_dados.
-- A sincronização da Câmara grava origem_dados = 'camara_deputados' e preenche
-- coletado_em / dados_camara. O domínio usa 'demonstracao' e 'oficial'.

ALTER TABLE politicos ADD COLUMN IF NOT EXISTS origem_dados VARCHAR(80) DEFAULT 'demonstracao';
ALTER TABLE politicos ADD COLUMN IF NOT EXISTS coletado_em TIMESTAMPTZ;
ALTER TABLE politicos ADD COLUMN IF NOT EXISTS atualizado_em TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE politicos ADD COLUMN IF NOT EXISTS dados_camara JSONB;

ALTER TABLE politicos ALTER COLUMN origem_dados TYPE VARCHAR(80);
UPDATE politicos SET origem_dados = 'demonstracao' WHERE origem_dados IS NULL;
ALTER TABLE politicos ALTER COLUMN origem_dados SET DEFAULT 'demonstracao';
ALTER TABLE politicos ALTER COLUMN origem_dados SET NOT NULL;

UPDATE politicos SET atualizado_em = NOW() WHERE atualizado_em IS NULL;
ALTER TABLE politicos ALTER COLUMN atualizado_em SET DEFAULT NOW();
ALTER TABLE politicos ALTER COLUMN atualizado_em SET NOT NULL;

ALTER TABLE politicos DROP CONSTRAINT IF EXISTS ck_politicos_origem_dados;
ALTER TABLE politicos
    ADD CONSTRAINT ck_politicos_origem_dados
        CHECK (origem_dados IN ('demonstracao', 'oficial', 'camara_deputados'));

-- O modelo Despesa.categoria é VARCHAR(160); 003_dominio criou VARCHAR(80).
ALTER TABLE despesas ALTER COLUMN categoria TYPE VARCHAR(160);

INSERT INTO schema_migrations (version, description)
VALUES (
    '005_reconciliar_politicos',
    'Alinha origem, coleta da Câmara e tamanho de categoria de despesa'
)
ON CONFLICT (version) DO NOTHING;
