# Voto Transparente

Plataforma estudantil apartidária de transparência política e educação cidadã. A aplicação utiliza React/JavaScript, Flask/Python, PostgreSQL e Docker Compose.

## 1. Equipe e participação no desenvolvimento

O projeto foi desenvolvido pelo seguinte grupo:

| Integrante | Participação no projeto |
|---|---|
| **Lara Leticia Jung Appel** | Desenvolvimento do frontend em React e JavaScript; criação e manutenção das páginas e componentes do site; integração da interface com a API Flask; ajustes na comunicação entre frontend e backend e melhorias de navegação, responsividade e funcionamento da aplicação. |
| **Carina Vitória Muller** | Desenvolvimento do módulo de integração com fontes oficiais de dados políticos, com foco inicial na API de Dados Abertos da Câmara dos Deputados; organização, normalização, importação e atualização dos dados no PostgreSQL; tratamento de falhas e registro das sincronizações. |
| **Kaiky Vieira** | Desenvolvimento da funcionalidade Minha Colinha Eleitoral em conjunto com a equipe e implementação das páginas individuais dos políticos, organizando a apresentação das informações de cada representante. |
| **Marya Reis** | Desenvolvimento da funcionalidade Minha Colinha Eleitoral em React e JavaScript, incluindo pesquisa e seleção de candidatos, organização das escolhas por cargo, edição e remoção de escolhas, armazenamento local e versão para impressão. |
| **Wesly Ribeiro** | Integração final dos módulos do sistema; auditoria da estrutura do projeto; verificação da comunicação entre frontend, backend e banco de dados; identificação e correção de incompatibilidades; revisão de configurações, testes e documentação técnica. |

As atividades relacionadas à Colinha Eleitoral foram desenvolvidas de forma complementar por Kaiky Vieira e Marya Reis. A descrição acima resume as responsabilidades informadas pela equipe.

## 2. Requisitos para execução

- Windows com Docker Desktop em execução e Docker Compose v2.
- Conexão com a internet para baixar imagens, dependências e sincronizar fontes públicas.
- As portas padrão `3000` (frontend), `5001` (API) e `5433` (PostgreSQL publicado no host) devem estar disponíveis. As portas podem ser alteradas no `.env`.

## 3. Instalação e execução

No PowerShell, dentro da pasta do repositório:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
docker compose up --build -d
docker compose ps
```

Na primeira execução, o Compose baixa e constrói os serviços, aplica as migrações e importa `database/seeds/demonstracao.json` quando `IMPORTAR_DADOS_DEMO=1`.

Aguarde os serviços `db`, `backend` e `frontend` ficarem `healthy`.

## 4. Acesso à aplicação

Após iniciar os serviços:

- **Frontend:** http://localhost:3000
- **API e saúde do banco:** http://localhost:5001/api/health

O exemplo publica o backend em `5001` e o PostgreSQL em `5433`. Dentro da rede Docker, Flask e PostgreSQL escutam em `5000` e `5432`.

Se alterar `BACKEND_PORT`, atualize `VITE_API_URL` para a mesma porta publicada e `FRONTEND_ORIGIN` para a origem efetiva do frontend. Reinicie o serviço frontend depois de alterar variáveis Vite.

`DATABASE_URL` utiliza `db:5432` dentro do Compose e não deve utilizar a porta publicada no host.

## 5. Publicação

O frontend foi publicado no GitHub Pages; a API Flask/backend é preparada para a Vercel com PostgreSQL externo na Neon.

Consulte [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) para as configurações, variáveis de ambiente e passos manuais de inicialização do banco.

O Docker Compose permanece como ambiente de desenvolvimento local.

**Importante:** (https://laraappel.github.io/Politize_trabalho_dw)

## 6. Segurança

O arquivo `.env` é local: não o compartilhe nem o versione. Os valores de `.env.example` são somente para desenvolvimento.

Esta stack utiliza o servidor de desenvolvimento Flask com `FLASK_DEBUG=1`, não possui autenticação geral de usuários e não deve ser exposta como serviço de produção.

Para produção, seria necessário configurar servidor WSGI, HTTPS, segredos fortes, controle de acesso e infraestrutura apropriada.

Para parar a aplicação:

```powershell
docker compose down
```

Esse comando preserva o volume do PostgreSQL.

**Atenção:** `docker compose down -v` apaga o banco local e só deve ser utilizado quando quiser descartar os dados e inicializar o banco novamente.

Para acompanhar os registros de execução:

```powershell
docker compose logs -f backend
docker compose logs -f frontend
```

## 7. Funcionalidades disponíveis

O Voto Transparente apresenta os seguintes recursos:

- Pesquisa de políticos por nome, cargo, partido e UF, com paginação.
- Perfil individual com mandatos, projetos, votações, despesas, fontes e notícias relacionadas.
- Transparência com filtros de despesas por categoria, UF e período; valores ausentes permanecem ausentes.
- Notícias com filtros, classificação contextual, links para as matérias e coleta manual de fontes autorizadas.
- Colinha eleitoral por ano e cargo, com busca por nome, número e partido, edição, remoção e impressão.
- Armazenamento das escolhas e anotações da colinha apenas no `localStorage` do navegador.
- Fotografias carregadas por URLs oficiais da Câmara dos Deputados e do Senado Federal, sem guardar os arquivos de imagem no PostgreSQL.
- Importação idempotente de pacotes JSON de demonstração ou oficiais.
- Consulta dos dados importados da Câmara dos Deputados.
- Consulta da lista de senadores em exercício do Senado Federal.
- Importação oficial dos resultados eleitorais do TSE para candidatos eleitos em 2022 e 2024.

O conjunto importado por padrão é fictício e está identificado como demonstração. A carga oficial do TSE é manual e não é executada automaticamente na inicialização.

## 8. Fontes de dados

O projeto utiliza fontes oficiais e públicas para obter informações políticas.

| Fonte | Dados integrados | Referência |
|---|---|---|
| Câmara dos Deputados | Deputados, partidos, histórico, proposições e despesas; importação local manual. | [API de Dados Abertos](https://dadosabertos.camara.leg.br/api/v2) |
| Senado Federal | Lista de senadores em exercício, partido, UF e identificador; sincronização manual. | [Dados Abertos do Senado](https://legis.senado.leg.br/dadosabertos/senador/lista/atual) |
| TSE | Candidaturas com resultado eleito dos arquivos de 2022 e 2024. | [Portal de Dados Abertos do TSE](https://dadosabertos.tse.jus.br/) |
| Agência Brasil / EBC | Metadados de notícias por RSS nas editorias autorizadas. | [Feed RSS de Política](https://agenciabrasil.ebc.com.br/rss/politica/feed.xml) |
| Demonstração | Registros fictícios identificados como demonstração. | `database/seeds/demonstracao.json` |

A integração com o TSE não inclui todos os concorrentes nem votos nominais. Também não representa cobertura completa de todas as eleições brasileiras.

O navegador carrega as fotos por HTTPS diretamente dos domínios oficiais da Câmara e do Senado. A aplicação não persiste os arquivos de imagem no PostgreSQL.

Consulte os detalhes de cobertura e limitações em:

- [Integração com a Câmara](docs/CAMARA.md)
- [Integração com o TSE](docs/TSE.md)
- [Integração com notícias](docs/NOTICIAS.md)

## 9. Importação e atualização dos dados

As operações abaixo são manuais e devem ser executadas com a stack ativa.

As migrações e o seed de demonstração são executados automaticamente pelo `entrypoint` durante a inicialização. Os demais comandos não são disparados por requisições HTTP.

```powershell
# Reaplicar migrações ainda não registradas
docker compose exec -T backend flask --app wsgi migrate

# Importar senadores atualmente em exercício
docker compose exec -T backend flask --app wsgi sincronizar-senado

# Carga inicial da Câmara
docker compose exec -T backend flask --app wsgi importar-camara-inicial

# Atualizar Câmara para um ano específico
docker compose exec -T backend flask --app wsgi atualizar-camara --ano 2026

# Importar/atualizar resultados eleitos do TSE
docker compose exec -T backend flask --app wsgi sincronizar-tse --anos 2022,2024

# Coletar notícias das fontes autorizadas
docker compose exec -T backend flask --app wsgi coletar-noticias

# Importar um pacote JSON de dados compatível
docker compose exec -T backend flask --app wsgi importar-dados --arquivo /database/seeds/demonstracao.json
```

As cargas da Câmara podem levar tempo e gerar muitas requisições. Consulte `docs/CAMARA.md` antes de importar intervalos históricos.

A coleta de notícias não possui agendador embutido. Os registros de sincronização da Câmara ficam disponíveis em `GET /api/data-sync-logs`.

## 10. Requisitos funcionais

Os requisitos funcionais descrevem as funcionalidades e os comportamentos que o sistema deve oferecer aos usuários.

| ID | Requisito funcional |
|---|---|
| RF01 | O sistema deve apresentar uma página inicial com acesso às principais áreas da aplicação. |
| RF02 | Permitir listar e pesquisar políticos, com filtros por nome, cargo, partido e UF, além de paginação. |
| RF03 | Apresentar o perfil individual de cada político, incluindo informações disponíveis sobre mandatos, projetos, votações, despesas, fontes e notícias relacionadas. |
| RF04 | Disponibilizar uma área de transparência com filtros de despesas por categoria, UF e período. |
| RF05 | Disponibilizar notícias associadas aos políticos, com filtros por político, veículo, assunto, natureza e período. |
| RF06 | Permitir acessar as notícias por meio de links para os veículos de origem. |
| RF07 | Classificar notícias por natureza: fato documentado, alegação, opinião, investigação ou não classificado. |
| RF08 | Permitir operações editoriais de revisão de associações, alteração da natureza das notícias e registro de atualizações mediante token administrativo. |
| RF09 | Oferecer uma colinha eleitoral para consulta e organização de candidatos por ano e cargo, permitindo editar, remover e imprimir as escolhas. |
| RF10 | Armazenar as escolhas da colinha eleitoral localmente no navegador, sem sincronização com o servidor. |
| RF11 | Consultar dados previamente importados da Câmara dos Deputados, incluindo deputados, despesas, proposições, partidos e registros de sincronização. |
| RF12 | Permitir sincronizar a lista atual de senadores em exercício. |
| RF13 | Permitir importar dados eleitorais do TSE referentes aos anos de 2022 e 2024, respeitando os limites da integração. |
| RF14 | Permitir importar pacotes JSON de demonstração ou outros dados compatíveis para o banco de dados. |
| RF15 | Disponibilizar um endpoint de saúde para verificar o funcionamento da API e a conexão com o banco de dados. |

## 10. Requisitos não funcionais

Os requisitos não funcionais definem as características de qualidade, segurança, organização e funcionamento do sistema.

| ID | Requisito não funcional |
|---|---|
| RNF01 — Arquitetura | O sistema deve separar a interface, a API e a camada de persistência, utilizando React/Vite, Flask e PostgreSQL. |
| RNF02 — Implantação | O ambiente de desenvolvimento deve permitir inicialização por meio do Docker Compose. |
| RNF03 — Compatibilidade | O projeto deve oferecer instruções de execução no Windows, utilizando PowerShell ou WSL e Docker Desktop. |
| RNF04 — Comunicação | A API deve realizar a comunicação com o frontend utilizando JSON e rotas HTTP documentadas, com datas no formato ISO 8601. |
| RNF05 — Segurança de credenciais | Credenciais e tokens não devem ser publicados no repositório nem enviados ao frontend. |
| RNF06 — Controle de acesso | As operações administrativas relacionadas às notícias devem exigir um token válido de administrador. |
| RNF07 — Segurança de produção | A publicação deve utilizar HTTPS, credenciais seguras, CORS restrito e infraestrutura adequada. |
| RNF08 — Integridade dos dados | Os dados oficiais devem preservar a identificação da fonte e a URL de referência, quando disponíveis. |
| RNF09 — Atualização | As importações e coletas de dados externos devem ocorrer de maneira controlada, sem depender das requisições normais dos usuários. |
| RNF10 — Desempenho | As listagens de dados devem possuir paginação e limites de consulta para evitar carregamentos excessivos. |
| RNF11 — Manutenibilidade | O código deve ser organizado em módulos, serviços, adaptadores, rotas, testes e documentação. |
| RNF12 — Testabilidade | O projeto deve possuir testes automatizados e permitir a verificação da compilação do frontend. |
| RNF13 — Privacidade | As escolhas realizadas na colinha eleitoral devem permanecer armazenadas localmente no dispositivo do usuário, sem envio ao backend. |
| RNF14 — Disponibilidade e integridade das informações | A interface deve diferenciar dados ausentes de valores conhecidos, evitando apresentar informações inventadas ou incorretas. |

## 11. Restrições e limitações conhecidas

- O sistema não possui autenticação geral de usuários.
- A colinha eleitoral é armazenada localmente no navegador e não é sincronizada entre dispositivos.
- A coleta de notícias é realizada manualmente.
- As importações da Câmara, do Senado e do TSE dependem de execução manual.
- A integração do TSE contempla os anos de 2022 e 2024, dentro dos limites documentados.
- Algumas informações, como remuneração, patrimônio e propostas de campanha, ainda não possuem integração completa.
- Os dados fictícios utilizados para demonstração devem estar identificados como demonstração.
- O ambiente Docker Compose é destinado ao desenvolvimento local e não deve ser utilizado diretamente como ambiente de produção.

## 12. Testes e verificações

Com a stack em execução:

```powershell
# Executar testes do backend
docker compose exec -T backend pytest -c /app/pytest.ini /tests -q

# Verificar build do frontend
docker compose exec -T frontend npm run build
```

O primeiro comando executa testes unitários e de integração contra o PostgreSQL da stack. Inclui testes de filtros, perfis, integrações e segurança editorial.

O segundo comando verifica a compilação do frontend.

O contrato completo das rotas, métodos, parâmetros e respostas está em [docs/API.md](docs/API.md).

Outras documentações:

- [Banco de dados](database/README.md)
- [Ambiente de desenvolvimento](docs/AMBIENTE.md)
- [Arquitetura](docs/ARQUITETURA.md)
- [Convenções de desenvolvimento](docs/CONVENCOES.md)

## 13. Estrutura do projeto

A organização principal do repositório é:

```text
frontend/                  Interface React/Vite
backend/                   API Flask e regras de negócio
database/init/              Esquema inicial do banco
database/migrations/        Migrações SQL
database/seeds/             Dados de demonstração
tests/                      Testes unitários e de integração
docs/                       Documentação do projeto
```

Leia `docs/CONVENCOES.md` antes de criar arquivos novos.

## 14. Documentação e links

- [Requisitos funcionais e não funcionais](docs/REQUISITOS.md)
- [Contrato e rotas da API](docs/API.md)
- [Arquitetura do sistema](docs/ARQUITETURA.md)
- [Configuração do ambiente local](docs/AMBIENTE.md)
- [Banco de dados e importação](database/README.md)
- [Publicação (GitHub Pages/Vercel)](docs/DEPLOYMENT.md)
- [Integração com a Câmara dos Deputados](docs/CAMARA.md)
- [Integração com o Senado Federal](docs/TSE.md)
- [Coleta e classificação de notícias](docs/NOTICIAS.md)
- [Convenções de desenvolvimento](docs/CONVENCOES.md)

**Repositório do projeto no GitHub:**

https://github.com/laraappel/Politize_trabalho_dw

**Link público da aplicação:** [acrescentar após a publicação e validação do GitHub Pages.](https://laraappel.github.io/Politize_trabalho_dw)

**Vídeo de apresentação no YouTube:** acrescentar após o envio do vídeo.

---

**Voto Transparente — Informação política acessível, transparência e cidadania.**