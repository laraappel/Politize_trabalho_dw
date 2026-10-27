# Ambiente de desenvolvimento

## Subir

```bash
cp .env.example .env
docker compose up --build
```

Recarga automática:

- Backend: o diretório `backend/` é montado no container; o Flask recarrega ao salvar arquivos.
- Frontend: o diretório `frontend/` é montado; o Vite recarrega ao salvar arquivos. `node_modules` fica em volume próprio para não sobrescrever as dependências do Linux.

## Parar

```bash
docker compose down
```

## Logs

```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
```

## Health checks

O Compose declara health checks para os três serviços. Confira:

```bash
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

## Windows

Execute os comandos no PowerShell ou no WSL. O Docker Desktop precisa estar em execução. O Vite usa polling de arquivos (`CHOKIDAR_USEPOLLING` e `server.watch.usePolling`) para detectar mudanças em pastas montadas no Windows.
