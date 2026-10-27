# Arquitetura inicial

## Visão geral

O Voto Transparente é uma aplicação web em três serviços:

1. **frontend**: interface React servida pelo Vite em desenvolvimento.
2. **backend**: API REST Flask, JSON, prefixo `/api`.
3. **db**: PostgreSQL 16, persistido em volume Docker.

O navegador fala com o frontend em `http://localhost:3000` e com a API em `http://localhost:5000`. O CORS do backend aceita apenas a origem definida em `FRONTEND_ORIGIN`.

Dentro da rede Docker, o backend acessa o banco pelo hostname `db`.

```
Navegador  -->  frontend (React)
Navegador  -->  backend (Flask) --> PostgreSQL
```

## Decisões desta etapa

- React com JavaScript (sem TypeScript), para reduzir a curva da equipe.
- Vite em vez de Create React App, por recarga rápida e suporte simples no Docker.
- Flask com application factory e blueprints, para cada módulo registrar suas rotas sem editar um único arquivo gigante.
- SQLAlchemy já configurado, mas sem modelos de domínio nesta etapa.
- Sem autenticação, scraping de notícias ou integração eleitoral.

## Contratos da API

- Respostas em JSON.
- Datas em ISO 8601.
- Erros no formato `{ "error": "codigo_estavel", "message": "texto para humanos" }`.
- Códigos HTTP semânticos: 200, 400, 404, 405, 500, 503.

O endpoint `GET /api/health` reporta **separadamente**:

- `api.status`: funcionamento do processo Flask.
- `database.status`: conectividade com o PostgreSQL (`ok` ou `unavailable`).
- `status`: `ok` se ambos estão bem; `degraded` se a API sobe mas o banco falha (HTTP 503).
