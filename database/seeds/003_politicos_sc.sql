-- Carga inicial de políticos de Santa Catarina para o Voto Transparente.
-- Fontes oficiais consultadas em 29/10/2026:
-- Governo de SC: https://agenda.scc.sc.gov.br/site/colegiado-de-governo
-- Senado Federal (senadores por UF): https://www25.senado.leg.br/web/senadores/por-uf/-/uf/SC
-- ALESC (deputados da legislatura atual): https://alesc.sc.gov.br/deputados/
--
-- A carga é idempotente: não insere outro registro com o mesmo nome_completo.
-- Confira os dados nas fontes oficiais periodicamente; partido e exercício de mandato podem mudar.
-- Esta carga inicial contém 20 registros: governador, 3 senadores e 16 deputados estaduais.
-- Deputados federais podem ser adicionados em uma próxima carga usando a fonte oficial da Câmara.

BEGIN;

WITH dados (nome_completo, nome_urna, apelidos, cargo, uf, partido) AS (
    VALUES
    ('Jorginho dos Santos Mello', 'Jorginho Mello', ARRAY['Jorginho','Jorginho Mello']::TEXT[], 'Governador', 'SC', 'PL'),
    ('Esperidião Amin Helou Filho', 'Esperidião Amin', ARRAY['Esperidião Amin','Amin']::TEXT[], 'Senador', 'SC', 'PP'),
    ('Ivete da Silveira', 'Ivete da Silveira', ARRAY['Ivete']::TEXT[], 'Senadora', 'SC', 'MDB'),
    ('Jorge Seif Junior', 'Jorge Seif', ARRAY['Jorge Seif','Seif']::TEXT[], 'Senador', 'SC', 'PL'),
    ('Ana Caroline Campagnolo', 'Ana Campagnolo', ARRAY['Ana Campagnolo','Campagnolo']::TEXT[], 'Deputada Estadual', 'SC', 'PL'),
    ('Altair Silva', 'Altair Silva', ARRAY['Altair']::TEXT[], 'Deputado Estadual', 'SC', 'PP'),
    ('Luciane Maria Carminatti', 'Luciane Carminatti', ARRAY['Luciane Carminatti','Carminatti']::TEXT[], 'Deputada Estadual', 'SC', 'PT'),
    ('Antídio Aleixo Lunelli', 'Antídio Lunelli', ARRAY['Antídio Lunelli','Lunelli']::TEXT[], 'Deputado Estadual', 'SC', 'MDB'),
    ('Mauro de Nadal', 'Mauro de Nadal', ARRAY['Mauro de Nadal','Mauro Nadal']::TEXT[], 'Deputado Estadual', 'SC', 'MDB'),
    ('Fernando Krelling', 'Fernando Krelling', ARRAY['Krelling']::TEXT[], 'Deputado Estadual', 'SC', 'MDB'),
    ('Jerry Edson Comper', 'Jerry Comper', ARRAY['Jerry Comper','Jerry']::TEXT[], 'Deputado Estadual', 'SC', 'MDB'),
    ('Paulinha', 'Paulinha', ARRAY['Paulinha']::TEXT[], 'Deputada Estadual', 'SC', 'Podemos'),
    ('José Milton Scheffer', 'Zé Milton', ARRAY['Zé Milton','José Milton']::TEXT[], 'Deputado Estadual', 'SC', 'PP'),
    ('Mário Sérgio Motta', 'Mário Motta', ARRAY['Mário Motta','Mario Motta']::TEXT[], 'Deputado Estadual', 'SC', 'PSD'),
    ('Jessé de Faria Lopes', 'Jessé Lopes', ARRAY['Jessé Lopes','Jesse Lopes']::TEXT[], 'Deputado Estadual', 'SC', 'PL'),
    ('Julio César Garcia', 'Julio Garcia', ARRAY['Julio Garcia','Júlio Garcia']::TEXT[], 'Deputado Estadual', 'SC', 'PSD'),
    ('Marcos Vieira', 'Marcos Vieira', ARRAY['Marcos Vieira']::TEXT[], 'Deputado Estadual', 'SC', 'PSDB'),
    ('Carlos Humberto Metzner Silva', 'Carlos Humberto', ARRAY['Carlos Humberto']::TEXT[], 'Deputado Estadual', 'SC', 'PL'),
    ('Ivan Naatz', 'Ivan Naatz', ARRAY['Ivan Naatz','Naatz']::TEXT[], 'Deputado Estadual', 'SC', 'PL'),
    ('Volnei Weber', 'Volnei Weber', ARRAY['Volnei Weber']::TEXT[], 'Deputado Estadual', 'SC', 'MDB')
)
INSERT INTO politicos (nome_completo, nome_urna, apelidos, cargo, uf, partido)
SELECT d.nome_completo, d.nome_urna, d.apelidos, d.cargo, d.uf, d.partido
FROM dados d
WHERE NOT EXISTS (
    SELECT 1 FROM politicos p
    WHERE lower(trim(p.nome_completo)) = lower(trim(d.nome_completo))
);

COMMIT;

-- Conferência após a carga:
-- SELECT cargo, COUNT(*) FROM politicos WHERE uf = 'SC' GROUP BY cargo ORDER BY cargo;
-- SELECT id, nome_completo, nome_urna, cargo, partido, uf FROM politicos WHERE uf = 'SC' ORDER BY cargo, nome_urna;
