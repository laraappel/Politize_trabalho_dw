# Banco de dados

Scripts SQL e migrações do PostgreSQL.

- `init/` contém scripts executados automaticamente na **primeira** criação do volume Docker.
- Novas migrações devem ser arquivos numerados, por exemplo `002_politicos.sql`.
- Não altere scripts já aplicados em ambientes compartilhados; crie um arquivo novo.

Para recriar o banco do zero em desenvolvimento (apaga dados locais):

```bash
docker compose down -v
docker compose up --build
```
