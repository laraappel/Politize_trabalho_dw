# Banco de dados

Scripts SQL e migrações do PostgreSQL.

- `init/` contém scripts executados automaticamente na **primeira** criação do volume Docker.
- `01_schema.sql` cria a tabela de controle `schema_migrations`.
- `migrations/002_noticias.sql` cria o cadastro compartilhado mínimo de políticos e as tabelas de notícias.
- `migrations/003_dominio.sql` estende políticos e cria mandatos, projetos, votações e despesas.
- `migrations/003_camara.sql` complementa políticos e cria as tabelas da Câmara, inclusive `data_sync_logs`.
- `migrations/004_integridade_dados.sql` valida proveniência oficial, períodos e identificadores.
- `migrations/005_reconciliar_politicos.sql` alinha `origem_dados`, a coleta da Câmara e o tamanho de `despesas.categoria`.
- `migrations/006_fontes_dados.sql` cria `data_sources`, `data_source_sync_logs` e `partidos`.
- O comando `flask migrate` aplica os arquivos `*.sql` da pasta pelo prefixo numérico. Entre os dois arquivos `003`, `003_dominio` roda antes de `003_camara`.
- Novas migrações devem usar um prefixo numérico sequencial; cada arquivo registra a própria versão em `schema_migrations`.
- Não altere scripts já aplicados em ambientes compartilhados; crie um arquivo novo.

## Importar dados

O seed fictício é importado automaticamente na inicialização quando `IMPORTAR_DADOS_DEMO=1`. Para repetir a importação:

```powershell
docker compose exec backend flask --app wsgi importar-dados --arquivo /database/seeds/demonstracao.json
```

Um pacote JSON tem a forma `{ "versao": 1, "politicos": [...] }`; cada político pode conter `mandatos`, `projetos`, `votacoes`, `despesas` e notícias. As chaves e campos são exemplificados em [seeds/demonstracao.json](seeds/demonstracao.json). A importação é idempotente para as chaves naturais usadas pelo esquema. Registros `oficial` exigem `fonte_nome` e `fonte_url` HTTP(S); valores financeiros podem ser `null`. Datas de início e fim devem ser consistentes.

## Recriar o banco local

Este procedimento apaga os dados armazenados no volume:

```bash
docker compose down -v
docker compose up --build
```

Use-o apenas quando realmente quiser descartar o banco local.
