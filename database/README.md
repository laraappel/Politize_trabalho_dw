# Banco de dados

Scripts SQL e migrações do PostgreSQL.

- `init/` contém scripts executados automaticamente na **primeira** criação do volume Docker.
- `01_schema.sql` cria a tabela de controle `schema_migrations`.
- `migrations/002_noticias.sql` cria o cadastro compartilhado mínimo de políticos e as tabelas de notícias.
- `migrations/003_dominio.sql` estende políticos e cria mandatos, projetos, votações e despesas.
- `migrations/004_integridade_dados.sql` valida proveniência oficial, períodos e identificadores.
- `migrations/011_cargos_eletivos_oficiais.sql` cria o cadastro de cargos com ano, situação e proveniência.
- `migrations/012_sigla_partido_candidatura.sql` preserva a sigla eleitoral por candidatura.
- Novas migrações devem usar um prefixo numérico sequencial; o comando do backend registra cada migração aplicada.
- Não altere scripts já aplicados em ambientes compartilhados; crie um arquivo novo.

## Importar dados

O seed fictício é importado automaticamente na inicialização quando `IMPORTAR_DADOS_DEMO=1`. Para repetir a importação:

```powershell
docker compose exec backend flask --app wsgi importar-dados --arquivo /database/seeds/demonstracao.json
```

Um pacote JSON tem a forma `{ "versao": 1, "politicos": [...] }`; cada político pode conter `mandatos`, `projetos`, `votacoes`, `despesas` e notícias. As chaves e campos são exemplificados em [seeds/demonstracao.json](seeds/demonstracao.json). A importação é idempotente para as chaves naturais usadas pelo esquema. Registros `oficial` exigem `fonte_nome` e `fonte_url` HTTP(S); valores financeiros podem ser `null`. Datas de início e fim devem ser consistentes.

Resultados eleitorais oficiais do TSE são importados separadamente pelo comando `flask --app wsgi sincronizar-tse`. Consulte [docs/TSE.md](../docs/TSE.md) para anos, arquivos e dados importados.

## Recriar o banco local

Este procedimento apaga os dados armazenados no volume:

```bash
docker compose down -v
docker compose up --build
```

Use-o apenas quando realmente quiser descartar o banco local.
