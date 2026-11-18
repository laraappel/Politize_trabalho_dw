# Arquitetura inicial

## Visão geral

O Voto Transparente é uma aplicação web em três serviços:

1. **frontend**: interface React servida pelo Vite em desenvolvimento.
2. **backend**: API REST Flask, JSON, prefixo `/api`.
3. **db**: PostgreSQL 16, persistido em volume Docker.

O navegador fala com o frontend em `http://localhost:3000` e com a API em `http://localhost:5001`. O CORS do backend aceita apenas a origem definida em `FRONTEND_ORIGIN`.

Dentro da rede Docker, o backend acessa o banco pelo hostname `db`.

```
Navegador  -->  frontend (React)
Navegador  -->  backend (Flask) --> PostgreSQL
```

## Módulos ativos

- React com JavaScript (sem TypeScript), para reduzir a curva da equipe.
- Vite em vez de Create React App, por recarga rápida e suporte simples no Docker.
- Flask com application factory e blueprints, para cada módulo registrar suas rotas sem editar um único arquivo gigante.
- SQLAlchemy mantém o cadastro compartilhado de políticos, mandatos, projetos, votações, despesas e notícias.
- Não há autenticação de usuários. O token administrativo é restrito às operações editoriais de notícias.
- A colinha fica no `localStorage` do navegador e não é enviada ao servidor.
- Coleta de notícias é manual e restrita a fontes autorizadas; consulte `docs/NOTICIAS.md`.

Modelos eleitorais em inglês (`Politician`, `Candidacy`, `PoliticalTerm` e outros) não estão importados pelo registro ativo de modelos, não têm migrações correspondentes e não fazem parte da API.

## Contratos da API

- Respostas em JSON.
- Datas em ISO 8601.
- Erros no formato `{ "error": "codigo_estavel", "message": "texto para humanos" }`.
- Códigos HTTP semânticos: 200, 400, 404, 405, 500, 503.

Rotas, filtros e campos estão documentados em `docs/API.md`. A serialização de datas, valores e origem é compartilhada pelo backend; o frontend centraliza requisições e erros em `frontend/src/api/client.js`.

O endpoint `GET /api/health` reporta **separadamente**:

- `api.status`: funcionamento do processo Flask.
- `database.status`: conectividade com o PostgreSQL (`ok` ou `unavailable`).
- `status`: `ok` se ambos estão bem; `degraded` se a API sobe mas o banco falha (HTTP 503).
