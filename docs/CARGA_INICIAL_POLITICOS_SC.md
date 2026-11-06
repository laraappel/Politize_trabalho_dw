# Carga inicial de políticos de Santa Catarina

O arquivo `database/seeds/003_politicos_sc.sql` cadastra 20 registros iniciais no banco já existente: governador, senadores e deputados estaduais.

## Aplicar no projeto já rodando

No CMD, entre na pasta `Politize_trabalho_dw` e execute:

```cmd
docker compose exec -T db psql -U voto -d voto_transparente < database\seeds\003_politicos_sc.sql
```

Depois confira:

```cmd
docker compose exec db psql -U voto -d voto_transparente -c "SELECT cargo, COUNT(*) FROM politicos WHERE uf='SC' GROUP BY cargo ORDER BY cargo;"
```

E rode a coleta:

```cmd
docker compose exec backend flask --app wsgi coletar-noticias --forcar
```

A carga evita inserir novamente um registro cujo `nome_completo` já exista. Ela não apaga nem altera registros existentes.

## Fontes oficiais consultadas em 29/10/2026

- Governo de Santa Catarina: https://agenda.scc.sc.gov.br/site/colegiado-de-governo
- Senado Federal: https://www25.senado.leg.br/web/senadores/por-uf/-/uf/SC
- Assembleia Legislativa de Santa Catarina: https://alesc.sc.gov.br/deputados/

Os dados de cargo e partido devem ser conferidos periodicamente nas páginas oficiais. Esta carga inicial ainda não inclui deputados federais nem cargos municipais; eles devem ser importados de suas fontes oficiais em uma etapa seguinte para cobrir integralmente esses níveis.
