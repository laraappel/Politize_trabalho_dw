# Voto Transparente

Plataforma brasileira de transparência política, educação cidadã e acompanhamento eleitoral. O projeto é apartidário, acessível e baseado em informações verificáveis.

Esta etapa entrega a **base técnica** para uma equipe de estudantes trabalhar em módulos independentes: frontend React, backend Flask, PostgreSQL e Docker.

## Requisitos

- Docker
- Docker Compose
- Git

## Como executar

1. Copie o arquivo de exemplo de variáveis de ambiente:

```bash
cp .env.example .env
```

No PowerShell:

```powershell
Copy-Item .env.example .env
```

2. Inicie os serviços:

```bash
docker compose up --build
```

3. Acesse:

- Frontend: [http://localhost:3000](http://localhost:3000)
- API de saúde: [http://localhost:5000/api/health](http://localhost:5000/api/health) (ou a porta definida em `BACKEND_PORT`)

4. Para parar os serviços, use `Ctrl+C` se estiverem em primeiro plano, ou:

```bash
docker compose down
```

Os dados do PostgreSQL ficam no volume `postgres_data`. Para apagar o banco local e recomeçar:

```bash
docker compose down -v
```

## Verificar o funcionamento

```bash
docker compose ps
curl http://localhost:5000/api/health
```

Resposta esperada da API:

```json
{
  "status": "ok",
  "api": { "status": "ok" },
  "database": { "status": "ok" },
  "service": "voto-transparente-api"
}
```

Testes de integração (com a stack no ar):

```bash
docker compose exec backend pytest /tests -q
```

## Estrutura

```
frontend/   aplicação React
backend/    API Flask
database/   scripts SQL
docs/       documentação da equipe
tests/      testes de integração
```

Leia `docs/CONVENCOES.md` antes de criar arquivos novos.

Módulo de notícias: `docs/NOTICIAS.md`.

Integração oficial com a Câmara dos Deputados: `docs/CAMARA.md` (comandos de carga inicial, atualização e rotas de consulta).
