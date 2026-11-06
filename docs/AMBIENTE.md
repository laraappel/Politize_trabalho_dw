# Ambiente de desenvolvimento

## Subir

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
docker compose up --build
```

Recarga automática:

- Backend: o diretório `backend/` é montado no container; o Flask recarrega ao salvar arquivos.
- Frontend: o diretório `frontend/` é montado; o Vite recarrega ao salvar arquivos. `node_modules` fica em volume próprio para não sobrescrever as dependências do Linux.

## Parar

```powershell
docker compose down
```

## Logs

```powershell
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
```

## Health checks

O Compose declara health checks para os três serviços. Confira:

```powershell
docker compose ps
```

Estados esperados: `healthy`.

## Portas padrão

| Serviço | Porta no host |
| --- | --- |
| Frontend | 3000 |
| Backend | 5000 |
| PostgreSQL | 5432 |

Altere no `.env` se houver conflito local. No Windows, as portas `5000` e `5432` costumam estar ocupadas; use `5001` e `5433` e atualize também `VITE_API_URL`.

## Dados e testes

O serviço backend aplica as migrações antes de iniciar e importa `database/seeds/demonstracao.json` por padrão. Para iniciar sem os dados fictícios, defina `IMPORTAR_DADOS_DEMO=0` no `.env`. Para importar outro pacote JSON, consulte [database/README.md](../database/README.md).

Com a stack ativa, execute os testes e a compilação:

```powershell
docker compose exec -T backend pytest -c /app/pytest.ini /tests -q
docker compose exec -T frontend npm run build
```

O `-c /app/pytest.ini` carrega a configuração e o caminho de importação Python do container; sem ele, o pytest iniciado apontando para `/tests` não encontra o pacote `app`.

## Windows

Execute os comandos no PowerShell ou no WSL. O Docker Desktop precisa estar em execução. O Vite usa polling de arquivos (`CHOKIDAR_USEPOLLING` e `server.watch.usePolling`) para detectar mudanças em pastas montadas no Windows.
