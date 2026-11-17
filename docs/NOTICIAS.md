# Módulo de notícias políticas

O módulo reúne **referências** a reportagens (título original, veículo, data, resumo curto quando permitido e link) e as vincula a perfis de políticos. Ele **nunca armazena o corpo das matérias**.

## Como usar

```bash
cp .env.example .env            # defina ADMIN_TOKEN se for usar as operações editoriais
docker compose up --build
docker compose exec backend flask --app wsgi migrate               # aplica database/migrations/*.sql
docker compose exec backend flask --app wsgi coletar-noticias      # coleta as fontes autorizadas
docker compose exec backend flask --app wsgi coletar-noticias --fonte agencia-brasil --forcar
```

Não há agendador embutido: rode `coletar-noticias` por cron ou tarefa agendada (o intervalo mínimo por fonte é `NOTICIAS_INTERVALO_MIN_SEGUNDOS`, padrão 900 s).

Testes:

```bash
PYTHONPATH=backend pytest tests/unit -q                                   # regras puras, sem banco
DATABASE_URL=... PYTHONPATH=backend pytest tests/integration/test_noticias_db.py   # banco migrado
```

## Auditoria das fontes

| Fonte | Situação | Base |
| --- | --- | --- |
| **Agência Brasil (EBC)** | **Ativa** | O serviço gov.br "Acessar notícias em tempo real gratuitamente" informa acesso livre e gratuito e reprodução permitida com crédito à Agência Brasil, exceto conteúdo de agências internacionais parceiras. A EBC publica feeds RSS por editoria. Guardamos só metadados + resumo curto e linkamos a matéria; itens que citam agências parceiras (Reuters, AFP, EFE, AP) ficam sem resumo. |
| G1 | Bloqueada | Não confirmei, em documentação oficial, API ou RSS com licença de redistribuição. |
| CNN Brasil | Bloqueada | Idem. |
| Folha de S.Paulo | Bloqueada | Idem. |
| Agência Câmara / Agência Senado | Não implementadas | Há páginas de RSS públicas, mas não verifiquei os termos de reutilização. Candidatas naturais a próximas fontes. |

"Bloqueada" significa: o adaptador existe (`fontes/nao_autorizadas.py`), levanta `FonteNaoAutorizada`, não faz requisição e a coleta é registrada como `ignorada`. Para habilitar um veículo: leia os termos oficiais, obtenha licença/chave se exigida e implemente `coletar()`. O status e a base de cada fonte são públicos em `GET /api/veiculos` e na página `/noticias`.

**Pendências de verificação** (não foi possível testar com rede aberta neste ambiente):

- As URLs dos feeds da Agência Brasil seguem o padrão `https://agenciabrasil.ebc.com.br/rss/<editoria>/feed.xml`. Confirme no primeiro uso; um erro HTTP aparece em `coletas_noticias.mensagem`.
- O parser foi testado com um RSS 2.0 **sintético**, não com o feed real.
- O padrão de URL de perfil do Senado usado para detectar identificadores (`associacao.py`) deve ser validado.

**Pluralidade:** a Agência Brasil é um veículo público federal. Uma única fonte não representa a diversidade da imprensa; adicionar veículos com licença é necessário antes de tratar a página como panorama equilibrado.

## Associação notícia ↔ político

Analisa apenas título e resumo (o corpo não é coletado, então o vínculo é naturalmente mais conservador). Cada associação guarda `status`, `grau_confirmacao`, `metodo`, `origem` e as `evidencias` (trechos).

| Situação | Status | Grau |
| --- | --- | --- |
| Identificador oficial (ID Câmara/Senado) nos links da matéria | confirmada | alta |
| Nome completo (2+ palavras) **e** título político próximo (deputado, senador, ministro…) e sem homônimo no cadastro | confirmada | alta |
| Nome completo sem contexto de cargo | pendente_revisao | média |
| Nome compartilhado por mais de um cadastro | pendente_revisao | baixa |
| Apelido + título político próximo | pendente_revisao | média/baixa |
| Apelido ou nome parcial sem contexto | ignorado | — |
| Revisão humana | confirmada ou rejeitada | manual |

- **Só `confirmada` aparece publicamente.** Pendentes ficam em `GET /api/noticias/revisao` (token admin).
- Decisões manuais e rejeições **não são sobrescritas** por novas coletas.
- Notícias sem nenhum político candidato **não são armazenadas**. Se não houver políticos cadastrados, a coleta registra isso e não grava nada (nenhum dado é inventado).

## Neutralidade e contexto

- A seleção depende apenas do vínculo com o político. Não há análise de sentimento e a ordenação é cronológica.
- `natureza`: `fato_documentado`, `alegacao`, `opiniao`, `investigacao`, `nao_classificado`. A heurística é conservadora, **nunca** atribui `fato_documentado` (exige revisão editorial) e registra a origem (`heuristica`/`editorial`). Precedência: opinião > investigação > alegação.
- A interface exibe um aviso por natureza (ex.: investigação "não implica culpa nem condenação") e informa que a classificação automática pode errar.
- **Desdobramentos:** `POST /api/noticias/<id>/atualizacoes` (desdobramento, correção, complemento, com link opcional). Mudanças de título feitas pelo veículo geram uma atualização automática com o título anterior.

## Duplicatas e URL original

`url_original` é preservada exatamente como veio. Para deduplicar usamos `url_canonica` (https, sem fragmento, sem `utm_*`/`fbclid`…, sem barra final), `(veículo, guid)` e `chave_dedup` (veículo + título normalizado + dia).

## Contrato da API

Listas seguem `{ items, total, page, per_page, pages }`. Erros: `{ error, message }`.

| Método e rota | Descrição |
| --- | --- |
| `GET /api/noticias` | Filtros: `politico` (id), `veiculo` (slug), `assunto` (slug), `natureza`, `de`/`ate` (AAAA-MM-DD, horário de Brasília), `ordem` (`recentes`\|`antigas`), `page`, `per_page` (máx. 50) |
| `GET /api/noticias/<id>` | Detalhe com evidências e atualizações |
| `GET /api/noticias/filtros` | Opções para os filtros (só o que tem notícia pública) |
| `GET /api/politicos/<id>/noticias` | Notícias do perfil (mesmos parâmetros) |
| `GET /api/veiculos` | Fontes, status e base de autorização |

Operações editoriais exigem o cabeçalho `X-Admin-Token` igual a `ADMIN_TOKEN`; sem a variável, retornam 403:
`GET /api/noticias/revisao`, `POST /api/noticias/<id>/politicos/<pid>/revisao` (`decisao`, `revisado_por`), `PATCH /api/noticias/<id>/natureza`, `POST /api/noticias/<id>/atualizacoes`.

## Limitações conhecidas

- Notícias compartilham a tabela `politicos` ativa; a migração `003_dominio.sql` a estende. O seed fictício é importado por padrão. Para fontes reais, mantenha associações revisáveis e origem rastreável.
- O token administrativo é compartilhado e provisório; em produção use autenticação real.
- Sem agendador, sem busca textual por palavra-chave e sem notificações.
