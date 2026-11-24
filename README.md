# Voto Transparente

Plataforma estudantil apartidária de transparência política e educação cidadã. A aplicação usa React/JavaScript, Flask/Python, PostgreSQL e Docker Compose.

## Requisitos

- Windows com Docker Desktop em execução e Docker Compose v2; os comandos abaixo usam PowerShell.
- Conexão com a internet para baixar imagens/dependências e sincronizar fontes públicas.
- As portas padrão `3000` (frontend), `5001` (API) e `5433` (PostgreSQL publicado no host) devem estar disponíveis. As portas podem ser alteradas no `.env`.

## Instalação e execução

No PowerShell, na pasta do repositório:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
docker compose up --build -d
docker compose ps
```

Na primeira execução, o Compose baixa/constrói os serviços, aplica as migrações e importa `database/seeds/demonstracao.json` quando `IMPORTAR_DADOS_DEMO=1`. Aguarde `db`, `backend` e `frontend` ficarem `healthy`.

Acesse:

- Aplicação: http://localhost:3000
- Saúde da API e do banco: http://localhost:5001/api/health

O exemplo publica o backend em `5001` e o PostgreSQL em `5433`; dentro da rede Docker, Flask e PostgreSQL escutam em `5000` e `5432`. Se alterar `BACKEND_PORT`, atualize `VITE_API_URL` para a mesma porta publicada e `FRONTEND_ORIGIN` para a origem efetiva do frontend. Reinicie o serviço frontend depois de alterar variáveis Vite. `DATABASE_URL` usa `db:5432` dentro do Compose e não deve usar a porta publicada no host.

O `.env` é local: não o compartilhe nem o versione. Os valores de `.env.example` são somente para desenvolvimento. Esta stack usa o servidor de desenvolvimento Flask com `FLASK_DEBUG=1`, não tem autenticação geral de usuários e não deve ser exposta como serviço de produção. Para produção, seria necessário configurar servidor WSGI, HTTPS, segredos fortes, controle de acesso e infraestrutura apropriada.

Para parar a stack iniciada em segundo plano:

```powershell
docker compose down
```

Esse comando preserva o volume do PostgreSQL. **`docker compose down -v` apaga o banco local** e só deve ser usado quando quiser descartar os dados e inicializar o banco novamente.

Para acompanhar logs ou parar serviços em segundo plano:

```powershell
docker compose logs -f backend
docker compose logs -f frontend
docker compose down
```

## Funcionalidades disponíveis

- Pesquisa de políticos por nome, cargo, partido e UF, com paginação.
- Perfil com mandatos, projetos, votações, despesas, fontes e notícias relacionadas.
- Transparência com filtros de despesas por categoria, UF e período; valores ausentes permanecem ausentes.
- Notícias com filtros, classificação contextual, links para as matérias e coleta manual de fontes autorizadas.
- Colinha eleitoral por ano e cargo, com busca por nome/número/partido, edição, remoção e impressão; escolhas e anotações ficam apenas no `localStorage` do navegador.
- Fotografias carregadas por URLs oficiais da Câmara dos Deputados e do Senado Federal, sem guardar os arquivos de imagem no PostgreSQL; perfis sem URL disponível exibem avatar padrão.
- Importação idempotente de pacotes JSON de demonstração ou oficiais.
- Consulta dos dados importados da Câmara dos Deputados. A carga é manual e está descrita em `docs/CAMARA.md`.
- Consulta da lista de senadores em exercício do Senado Federal; sincronização manual.
- Importação oficial dos resultados eleitorais do TSE para candidatos eleitos em 2022 e 2024, com ano e situação eleitoral. Consulte `docs/TSE.md`.

O conjunto importado por padrão é fictício e está identificado como demonstração. A carga oficial do TSE é manual; não é executada automaticamente na inicialização.

## Fontes de dados implementadas

| Fonte | Dados integrados | Referência oficial |
| --- | --- | --- |
| Câmara dos Deputados | Deputados, partidos, histórico, proposições e despesas; importação local manual. | [Dados Abertos — API v2](https://dadosabertos.camara.leg.br/api/v2) · [Swagger](https://dadosabertos.camara.leg.br/swagger/api.html) |
| Senado Federal | Lista de senadores em exercício, partido, UF e identificador; sincronização manual. | [Dados Abertos — lista atual](https://legis.senado.leg.br/dadosabertos/senador/lista/atual) |
| TSE | Candidaturas com resultado eleito dos arquivos de 2022 e 2024; não inclui todos os concorrentes nem votos nominais. | [Portal de Dados Abertos](https://dadosabertos.tse.jus.br/) · [2022](https://dadosabertos.tse.jus.br/dataset/candidatos-2022) · [2024](https://dadosabertos.tse.jus.br/dataset/candidatos-2024) |
| Agência Brasil / EBC | Metadados de notícias por RSS nas editorias autorizadas; a matéria permanece no site de origem. | [Feeds RSS](https://agenciabrasil.ebc.com.br/rss/politica/feed.xml) · [Termos de reutilização](https://www.gov.br/pt-br/servicos/acessar-noticias-em-tempo-real-gratuitamente) |
| Demonstração | Registros fictícios rotulados como demonstração; não representam dados reais. | [Seed local](database/seeds/demonstracao.json) |

O navegador carrega as fotos por HTTPS diretamente dos domínios oficiais da Câmara e do Senado. A aplicação não persiste os arquivos de imagem no PostgreSQL; alguns dados de origem incluem apenas URLs. Veja detalhes de cobertura, atualização e limitações em [docs/CAMARA.md](docs/CAMARA.md), [docs/TSE.md](docs/TSE.md) e [docs/NOTICIAS.md](docs/NOTICIAS.md).

## Importar e atualizar dados

As operações abaixo são manuais e devem ser executadas com a stack ativa. Migrações e seed de demonstração são executados automaticamente pelo `entrypoint` durante a inicialização; os demais comandos não são disparados por requisições HTTP.

```powershell
# Reaplicar apenas migrações ainda não registradas e sincronizar o cadastro de veículos
docker compose exec -T backend flask --app wsgi migrate

# Importar senadores atualmente em exercício
docker compose exec -T backend flask --app wsgi sincronizar-senado

# Carga inicial da Câmara; padrão: ano atual para despesas e proposições
docker compose exec -T backend flask --app wsgi importar-camara-inicial

# Atualizar Câmara para um ano específico
docker compose exec -T backend flask --app wsgi atualizar-camara --ano 2026

# Importar/atualizar resultados eleitos do TSE (anos suportados: 2022 e 2024)
docker compose exec -T backend flask --app wsgi sincronizar-tse --anos 2022,2024

# Coletar notícias das fontes autorizadas; --forcar ignora o intervalo mínimo
docker compose exec -T backend flask --app wsgi coletar-noticias

# Importar um pacote JSON de dados compatível
docker compose exec -T backend flask --app wsgi importar-dados --arquivo /database/seeds/demonstracao.json
```

As cargas da Câmara podem levar tempo e gerar muitas requisições; consulte [docs/CAMARA.md](docs/CAMARA.md) antes de importar intervalos históricos. A coleta de notícias não tem agendador embutido. Os registros de sincronização da Câmara ficam disponíveis em `GET /api/data-sync-logs`.

## Funcionalidades pendentes / limitações

- A importação do TSE cobre resultados de eleições de 2022 e 2024; outros anos não são inferidos.
- Remuneração, patrimônio declarado, propostas de campanha e votação/filiação eleitoral não têm fluxos completos disponíveis na interface.
- Coleta de notícias não é agendada; execute-a manualmente. A Agência Brasil é a única fonte autorizada implementada; outras fontes permanecem bloqueadas até verificação de licença.
- Projetos aceitam apenas um político vinculado; coautoria ainda não é suportada.
- Não há contas de usuário. A colinha fica no navegador e não é sincronizada.
- As rotas eleitorais de propostas, coautorias, remuneração e patrimônio estão implementadas, mas não há integração pública de carga completa para esses registros; podem retornar listas vazias.
- O frontend de políticos combina deputados importados da Câmara com os cargos eleitorais disponíveis. Não representa um cadastro completo de todos os agentes públicos do país.

## Testes e verificações

Com a stack em execução:

```powershell
docker compose exec -T backend pytest -c /app/pytest.ini /tests -q
docker compose exec -T frontend npm run build
```

O primeiro comando executa testes unitários e de integração contra o PostgreSQL da stack. Inclui testes de filtros, perfis, integrações e segurança editorial. O build valida o frontend. O contrato completo das rotas, métodos, parâmetros e respostas está em [docs/API.md](docs/API.md); banco e ambiente estão em [database/README.md](database/README.md) e [docs/AMBIENTE.md](docs/AMBIENTE.md).

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
