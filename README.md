# Voto Transparente

Plataforma estudantil apartidária de transparência política e educação cidadã. A aplicação usa React/JavaScript, Flask/Python, PostgreSQL e Docker Compose.

## Requisitos

- Docker Desktop em execução (Docker Compose v2 incluído)
- Git, para clonar o repositório

## Instalação e execução

No PowerShell, na pasta do repositório:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
docker compose up --build
```

Na primeira execução, o Compose baixa as imagens, constrói os serviços, cria o esquema do banco e importa os dados fictícios de demonstração. Aguarde os três serviços aparecerem como `healthy` em outro terminal:

```powershell
docker compose ps
```

Acesse:

- Aplicação: http://localhost:3000
- Saúde da API e do banco: http://localhost:5001/api/health

O exemplo publica o backend em `5001` e o PostgreSQL em `5433`. Dentro da rede Docker o Flask continua na porta `5000` e o Postgres na `5432`. `VITE_API_URL` precisa apontar para a porta que o navegador alcança (`http://localhost:5001`). Se alterar `BACKEND_PORT` ou `POSTGRES_PORT` no `.env`, atualize também `VITE_API_URL`. O arquivo `.env` é local e não deve ser compartilhado ou commitado. Os valores de exemplo são apenas para desenvolvimento local.

Para parar a stack em primeiro plano, pressione `Ctrl+C`; em seguida, execute:

```powershell
docker compose down
```

Esse comando preserva o volume do PostgreSQL. **`docker compose down -v` apaga o banco local** e só deve ser usado quando quiser descartar os dados e inicializar o banco novamente.

## Funcionalidades disponíveis

- Pesquisa de políticos por nome, cargo, partido e UF, com paginação.
- Perfil com mandatos, projetos, votações, despesas, fontes e notícias relacionadas.
- Transparência com filtros de despesas por categoria, UF e período; valores ausentes permanecem ausentes.
- Notícias com filtros, classificação contextual, links para as matérias e coleta manual de fontes autorizadas.
- Colinha eleitoral por ano e cargo, com busca por nome/número/partido, edição, remoção e impressão; escolhas e anotações ficam apenas no `localStorage` do navegador.
- Importação idempotente de pacotes JSON de demonstração ou oficiais.
- Consulta dos dados importados da Câmara dos Deputados. A carga é manual e está descrita em `docs/CAMARA.md`.
- Importação oficial dos resultados eleitorais do TSE para candidatos eleitos em 2022 e 2024, com ano e situação eleitoral. Consulte `docs/TSE.md`.

O conjunto importado por padrão é fictício e está identificado como demonstração. A carga oficial do TSE é manual; não é executada automaticamente na inicialização.

## Funcionalidades pendentes / limitações

- A importação do TSE cobre resultados de eleições de 2022 e 2024; outros anos não são inferidos.
- Remuneração, patrimônio declarado, propostas de campanha e votação/filiação eleitoral não têm fluxos completos disponíveis na interface.
- Coleta de notícias não é agendada; execute-a manualmente. A Agência Brasil é a única fonte autorizada implementada; outras fontes permanecem bloqueadas até verificação de licença.
- Projetos aceitam apenas um político vinculado; coautoria ainda não é suportada.
- Não há contas de usuário. A colinha fica no navegador e não é sincronizada.

## Testes e verificações

Com a stack em execução:

```powershell
docker compose exec -T backend pytest -c /app/pytest.ini /tests -q
docker compose exec -T frontend npm run build
```

O primeiro comando executa testes unitários e de integração contra o banco da stack. Mais detalhes sobre API, banco, importação e ambiente estão em [docs/API.md](docs/API.md), [database/README.md](database/README.md) e [docs/AMBIENTE.md](docs/AMBIENTE.md).

## Estrutura

- `frontend/`: interface React/Vite.
- `backend/`: API Flask e regras de negócio.
- `database/init/` e `database/migrations/`: esquema inicial e migrações SQL.
- `database/seeds/`: conjunto fictício de demonstração.
- `tests/`: testes unitários e de integração.
- `docs/`: contratos e guias do projeto.

Leia `docs/CONVENCOES.md` antes de criar arquivos novos.

Módulo de notícias: `docs/NOTICIAS.md`.

Integração oficial com a Câmara dos Deputados: `docs/CAMARA.md` (comandos de carga inicial, atualização e rotas de consulta).
