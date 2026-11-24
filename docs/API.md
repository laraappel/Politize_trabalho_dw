# Contrato da API

Este documento descreve as rotas Flask efetivamente registradas em `backend/app/routes/`. A API é JSON e usa o prefixo `/api`.

- Endereço padrão no navegador: `http://localhost:5001/api` (`VITE_API_URL` + `/api`).
- Dentro do Docker, o Flask atende na porta `5000`; a porta publicada no host vem de `BACKEND_PORT`.
- CORS permite somente as origens de `FRONTEND_ORIGIN` (lista separada por vírgulas); credenciais CORS não são habilitadas.
- As consultas públicas não exigem autenticação; não há contas de usuário. A fila `GET /noticias/revisao` e as operações editoriais são protegidas por `X-Admin-Token`.

## Formatos, paginação e erros

Rotas que usam a paginação comum (`page`, `per_page`) retornam:

```json
{"items": [], "total": 0, "page": 1, "per_page": 10, "pages": 0}
```

`page` começa em 1; `per_page` é 10 por padrão e aceita no máximo 50. A API da Câmara tem outro contrato: `pagina` (padrão 1) e `limite` (padrão 20, máximo 100), e normalmente responde com `dados` e `paginacao`.

Exceções de formato: `GET /noticias` retorna `pages` com valor mínimo 1 mesmo quando não há itens; `GET /noticias/revisao` retorna `items`, `total`, `page` e `per_page` sem o campo `pages`.

- Datas são ISO 8601; filtros de data aceitam `AAAA-MM-DD`.
- Valores financeiros são strings decimais ou `null`. `null` quer dizer não informado, não zero.
- Registros podem incluir `origem_dados`, `demonstracao` e `fonte: {nome, url}`.
- Erro de validação: `{ "error": "codigo", "message": "mensagem" }`, normalmente HTTP 400; recurso inexistente retorna 404.
- `/health` retorna 503 quando o banco está indisponível. Erros internos retornam HTTP 500.

## Rotas gerais e políticos

| Método e rota | Query/body | Resposta e comportamento |
| --- | --- | --- |
| `GET /health` | — | `{status, api: {status}, database: {status}, service}`; 200 saudável, 503 degradado. |
| `GET /politicos` | `q`, `cargo`, `partido`, `uf`, `page`, `per_page` | Envelope comum de resumos (`id`, nomes, cargo, UF, município, partido, IDs oficiais, proveniência e ano de referência). `q` busca nome civil/de urna; `uf` é sigla válida. |
| `GET /politicos/filtros` | — | `{cargos: [], partidos: [], ufs: []}`. |
| `GET /politicos/<politico_id>` | — | Perfil resumido com `apelidos`, `dados_oficiais`, `mandatos`, `projetos`, `votacoes`, `despesas` e `resumo_financeiro`. Despesas neste perfil são retornadas juntas, sem paginação. |
| `GET /politicos/<politico_id>/mandatos` | `page`, `per_page` | Envelope comum; período, cargo, esfera, partido, legislatura e proveniência. |
| `GET /politicos/<politico_id>/projetos` | `page`, `per_page` | Envelope comum; casa, número/ano, ementa, situação, data e URL oficial. |
| `GET /politicos/<politico_id>/votacoes` | `page`, `per_page` | Envelope comum; identificador, casa, data, ementa, voto e referências oficiais. |
| `GET /politicos/<politico_id>/despesas` | `categoria`, `uf`, `de`, `ate`, `page`, `per_page` | Envelope comum e `resumo_financeiro`; combina despesas locais e da Câmara quando há vínculo. Datas são inclusivas. |

O campo `dados_oficiais` do perfil contém `identificacao`, `cargos`, `candidaturas`, `mandatos` e `historico`, cada qual com ano de referência e fonte quando disponível. Ele não infere ocupação atual a partir de resultado eleitoral histórico.

## Cargos eleitorais e domínios eleitorais

| Método e rota | Query/body | Resposta e comportamento |
| --- | --- | --- |
| `GET /cargos-eletivos` | `q`, `cargo`, `esfera`, `partido`, `uf`, `municipio`, `situacao`, `ano`, `page`, `per_page` | Envelope de cargos (`politico_id`, nome, cargo, esfera, localidade, partido, `numero_candidato`, ano, situação, origem e fonte). `q` busca nome/nome de urna ou número de urna; números formados só por dígitos são correspondência exata. `municipio` aceita parte do nome. |
| `GET /cargos-eletivos/filtros` | — | `{cargos, esferas, ufs, municipios, anos, partidos, situacoes}` das linhas existentes. |
| `GET /partidos-cadastrados` | `q`, `page`, `per_page` | Envelope comum com sigla, nome, ID/URI da Câmara e proveniência; pode estar vazio se não houver partidos carregados. |
| `GET /partidos-cadastrados/<partido_id>` | — | Partido cadastrado ou 404. |
| `GET /politicos/<politico_id>/candidaturas` | `ano`, `page`, `per_page` | Envelope comum; inclui ano, cargo, UF/município, `nome_urna`, `numero_candidatura`, partido, resultado, votos e proveniência. |
| `GET /candidaturas/<candidatura_id>/propostas` | `page`, `per_page` | Envelope de propostas (`titulo`, `descricao`, `tema`, origem e fonte); 404 se a candidatura não existe. |
| `GET /projetos/<projeto_id>/coautorias` | `page`, `per_page` | Envelope de coautorias (`politico_id`, nome, papel e proveniência); 404 se o projeto não existe. |
| `GET /politicos/<politico_id>/remuneracoes` | `page`, `per_page` | Envelope de períodos e valores (`valor_bruto`, benefícios, descontos e líquido), com origem. |
| `GET /politicos/<politico_id>/patrimonio` | `ano`, `page`, `per_page` | Envelope de itens declarados (`ano_referencia`, tipo, descrição, valor, localização e origem). |

As candidaturas/cargos refletem somente os dados já importados. O TSE importa resultados eleitos em 2022 e 2024; o Senado sincroniza a lista atual de senadores. Os quatro domínios adicionais (propostas, coautorias, remuneração e patrimônio) têm consulta implementada, mas não possuem integração de carga completa nesta aplicação; portanto, podem retornar listas vazias. O frontend da colinha usa apenas os cargos e candidaturas disponíveis e salva escolhas no navegador. Não existe endpoint que receba ou sincronize a colinha.

## Transparência

| Método e rota | Query/body | Resposta e comportamento |
| --- | --- | --- |
| `GET /transparencia` | — | `{politicos, politicos_demonstracao, mandatos, projetos, votacoes, despesas, aviso}`; `despesas` inclui totais, valores ausentes, soma informada e divisão por categoria. |
| `GET /transparencia/despesas` | `categoria`, `uf`, `de`, `ate`, `page`, `per_page` | Envelope comum de despesas unificadas e `resumo_financeiro`. Os registros incluem categoria, descrição, valor, período, político, origem e fonte. Datas são inclusivas; `de` posterior a `ate` gera 400. |
| `GET /transparencia/filtros` | — | `{categorias: [], ufs: []}` presentes nos registros. |

O resumo financeiro nunca trata valor ausente como zero. Os registros oficiais da Câmara podem trazer `valor_liquido`, documento, fornecedor e identificador do documento.

## Notícias

Notícias públicas só são exibidas quando possuem associação confirmada a um político. A resposta resumida contém título/link original, veículo, data, resumo permitido, assunto, classificação da natureza, políticos confirmados e contagem de atualizações.

| Método e rota | Query/body | Resposta e comportamento |
| --- | --- | --- |
| `GET /noticias` | `politico`, `veiculo` (slug), `assunto` (slug), `natureza`, `de`, `ate`, `ordem`, `page`, `per_page` | Envelope comum; `ordem` aceita `recentes` (padrão) ou `antigas`. `natureza`: `fato_documentado`, `alegacao`, `opiniao`, `investigacao`, `nao_classificado`. |
| `GET /noticias/filtros` | — | Veículos, assuntos e políticos com notícias públicas; lista os códigos de natureza suportados. |
| `GET /noticias/<noticia_id>` | — | Detalhe público com evidências das associações e atualizações; 404 para notícia inexistente ou sem associação confirmada. |
| `GET /politicos/<politico_id>/noticias` | mesmos filtros de `GET /noticias`, exceto o ID vem da rota | Envelope das notícias confirmadas do perfil; 404 se o político não existe. |
| `GET /veiculos` | — | `{items: [...]}` com slug, nome, domínio, tipo, autorização, base de autorização, termos e última coleta. |
| `GET /noticias/revisao` | `page`, `per_page` + `X-Admin-Token` | `{items, total, page, per_page}` de associações pendentes, com notícia, político, grau, método e evidências. Requer token administrativo. |
| `POST /noticias/<noticia_id>/politicos/<politico_id>/revisao` | JSON `{ "decisao": "confirmar"|"rejeitar", "revisado_por": "..." }` + token | `{noticia_id, politico_id, status}`; exige revisor não vazio. |
| `PATCH /noticias/<noticia_id>/natureza` | JSON `{ "natureza": "..." }` + token | `{id, natureza, origem}`; natureza deve pertencer à lista acima. |
| `POST /noticias/<noticia_id>/atualizacoes` | JSON `{ "tipo": "desdobramento"|"correcao"|"complemento", "descricao": "...", "url_referencia"?: "https://...", "noticia_relacionada_id"?: 1, "criado_por"?: "..." }` + token | Registro da atualização; HTTP 201. `descricao` é obrigatória; URL opcional deve usar HTTP(S). |

As três operações de escrita e `GET /noticias/revisao` exigem `X-Admin-Token` igual a `ADMIN_TOKEN`. Se a variável não está configurada, recebem 403 (`admin_desabilitado`); token ausente/inválido quando configurado recebe 401. Não coloque esse token no bundle ou no frontend.

## Dados da Câmara dos Deputados

Estas rotas expõem os registros já importados no banco; não consultam a Câmara ao vivo. Paginação usa `pagina` (padrão 1) e `limite` (padrão 20, limitado a 100). Respostas de lista usam `dados` e `paginacao`.

| Método e rota | Query/body | Resposta e comportamento |
| --- | --- | --- |
| `GET /deputados` | `pagina`, `limite`, `q`, `uf`, `partido` | Lista de deputados com IDs locais/oficiais, nome, cargo, UF, partido e timestamps; `q` busca nome civil/de urna. |
| `GET /deputados/<id_camara>` | — | `{dados: deputado, mandatos: [], historico: []}`; histórico inclui `url_foto` oficial quando fornecida pela Câmara. |
| `GET /deputados/<id_camara>/despesas` | `pagina`, `limite`, `ano`, `mes`, `tipo_despesa` | `{dados: [], contexto: {ano, mes, tipo_despesa}, paginacao}`; contém fornecedor, valores, documento e URL oficial. |
| `GET /proposicoes` | `pagina`, `limite`, `ano`, `sigla_tipo` | Lista paginada com ID/URI da Câmara, tipo, número, ano, ementa, situação, data e autores. |
| `GET /partidos` | — | `{dados: [...]}` com sigla, nome e URI dos partidos importados da Câmara. |
| `GET /data-sync-logs` | `pagina`, `limite` | `{dados: [...]}` com fonte, entidade, operação, status, horários, contagens e mensagem da sincronização. |

## Fontes oficiais e importações

| Integração | Fonte / URL oficial | Carga disponível |
| --- | --- | --- |
| Câmara dos Deputados | [API Dados Abertos v2](https://dadosabertos.camara.leg.br/api/v2), [Swagger](https://dadosabertos.camara.leg.br/swagger/api.html) | `importar-camara-inicial` e `atualizar-camara`; detalhes e limites em [CAMARA.md](CAMARA.md). |
| Senado Federal | [Lista de parlamentares em exercício](https://legis.senado.leg.br/dadosabertos/senador/lista/atual) | `sincronizar-senado`; importa a lista atual, não o histórico completo. |
| TSE | [Portal de Dados Abertos](https://dadosabertos.tse.jus.br/), [pacote 2022](https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_2022.zip), [pacote 2024](https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_2024.zip) | `sincronizar-tse --anos 2022,2024`; somente situações que começam com `ELEITO`, sem votos nominais. Veja [TSE.md](TSE.md). |
| Agência Brasil / EBC | [RSS Política](https://agenciabrasil.ebc.com.br/rss/politica/feed.xml), [RSS Justiça](https://agenciabrasil.ebc.com.br/rss/justica/feed.xml), [termos de reutilização](https://www.gov.br/pt-br/servicos/acessar-noticias-em-tempo-real-gratuitamente) | `coletar-noticias`; apenas metadados e resumo curto permitido, sem texto integral. Ver [NOTICIAS.md](NOTICIAS.md). |
| Fotos oficiais | [Câmara](https://www.camara.leg.br/internet/deputado/bandep/204379.jpg), [Senado](https://www.senado.leg.br/senadores/img/fotos-oficiais/senador5672.jpg) | A interface busca arquivos remotos por identificadores/URLs oficiais; os arquivos de imagem não são armazenados no PostgreSQL. Metadados de URL podem constar nos dados de origem importados. |

Comandos de coleta/importação são CLI, não endpoints HTTP. O entrypoint aplica migrações e, por padrão, importa o seed de demonstração. As integrações externas são manuais:

```powershell
docker compose exec -T backend flask --app wsgi migrate
docker compose exec -T backend flask --app wsgi importar-dados --arquivo /database/seeds/demonstracao.json
docker compose exec -T backend flask --app wsgi sincronizar-fontes
docker compose exec -T backend flask --app wsgi sincronizar-senado
docker compose exec -T backend flask --app wsgi importar-camara-inicial
docker compose exec -T backend flask --app wsgi atualizar-camara --ano 2026
docker compose exec -T backend flask --app wsgi sincronizar-tse --anos 2022,2024
docker compose exec -T backend flask --app wsgi coletar-noticias
```

Consulte [README.md](../README.md), [AMBIENTE.md](AMBIENTE.md), [database/README.md](../database/README.md) e os guias de cada fonte para requisitos, limites e atualização de dados.
