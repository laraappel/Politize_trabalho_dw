# Integração com a Câmara dos Deputados

## Fonte e política de acesso

- Fonte: API oficial Dados Abertos da Câmara dos Deputados.
- Base: `https://dadosabertos.camara.leg.br/api/v2`.
- Documentação/Swagger: <https://dadosabertos.camara.leg.br/swagger/api.html>.
- Acesso: consultas HTTP GET públicas; esta integração não utiliza token nem credencial.
- O adaptador envia `Accept: application/json` e um `User-Agent` identificável.
- O cliente limita cada página a no máximo 100 itens (limite informado pelo Swagger), usa timeout, intervalo configurável e retentativas para HTTP 429/5xx e falhas temporárias.

## O que é importado

| Entidade local | Endpoint | Identificador preservado |
|---|---|---|
| `politicos` | `/deputados` e `/deputados/{id}` | `id_camara` |
| `partidos_camara` | `/partidos` | `id_partido_camara`, sigla e URI |
| `mandatos_camara` | `/deputados/{id}/historico` | ID do deputado, legislatura e chave de origem |
| `despesas_camara` | `/deputados/{id}/despesas?ano=...` | `idDocumento` quando fornecido; chave hash estável como fallback |
| `proposicoes_camara` | `/proposicoes` | `id_proposicao_camara` e URI |
| `data_sync_logs` | controle interno | ID local do log |

O módulo reaproveita a tabela `politicos` já criada pelo módulo de notícias, para não criar duas identidades locais para a mesma pessoa. O `id_camara` é mantido como identificador oficial e a chave `politicos.id` continua sendo a chave interna usada pelas relações existentes.

## Comandos

Execute dentro do container backend:

```bash
# Aplicar migrações pendentes e sincronizar o cadastro de veículos de notícias
docker compose exec backend flask --app wsgi migrate

# Carga inicial; por padrão consulta o ano atual para despesas e proposições
docker compose exec backend flask --app wsgi importar-camara-inicial

# Carga histórica delimitada, se necessário (pode demorar bastante)
docker compose exec backend flask --app wsgi importar-camara-inicial --ano-inicial 2022 --ano-final 2026

# Atualização incremental dos dados do ano atual
docker compose exec backend flask --app wsgi atualizar-camara

# Teste controlado: apenas dois deputados (não use como carga completa)
docker compose exec backend flask --app wsgi importar-camara-inicial --limite-deputados 2
```

As importações são comandos administrativos separados; nenhuma chamada HTTP de usuário inicia coleta externa.

## API interna do Voto Transparente

- `GET /api/deputados?pagina=1&limite=20&uf=SC&partido=...`
- `GET /api/deputados/{id_camara}` (inclui mandatos importados)
- `GET /api/deputados/{id_camara}/despesas?ano=2026&mes=1&tipo_despesa=...`
- `GET /api/proposicoes?ano=2026&sigla_tipo=PL`
- `GET /api/partidos`
- `GET /api/data-sync-logs?pagina=1&limite=20`

As despesas são devolvidas individualmente, com categoria e contexto temporal. A API não soma categorias diferentes automaticamente. Valores monetários são serializados como texto decimal para evitar perda de precisão. Campos ausentes permanecem `null`; zero só é mantido quando a fonte efetivamente informa zero.

## Atualização, duplicatas e falhas

- Chaves oficiais são preservadas em colunas próprias.
- Reimportações consultam as chaves de origem antes de inserir; registros existentes são atualizados.
- Campos `None` da fonte não sobrescrevem campos já preenchidos, evitando apagar informação válida por ausência momentânea.
- Cada entidade/execução gera uma linha em `data_sync_logs`, com status, contagens, horários e mensagem de falha.
- Despesas sem `idDocumento` recebem chave SHA-256 calculada sobre os dados recebidos e o ID do deputado; não se inventa identificador oficial.
- `coletado_em` registra a primeira coleta e `atualizado_em` acompanha a última atualização local do registro.

## Cobertura e lacunas

- A integração cobre somente a Câmara dos Deputados (esfera federal e somente deputados federais), não Senado, Assembleias Legislativas, Câmaras Municipais, eleições ou todos os agentes políticos brasileiros.
- O endpoint de histórico parlamentar representa as mudanças disponíveis na base da Câmara; não deve ser interpretado como histórico eleitoral completo.
- A documentação da Câmara informa que a CEAP está disponível desde 2008, mas a importação inicial deste módulo consulta somente os anos solicitados no comando. A carga padrão consulta apenas o ano corrente para evitar milhares de chamadas sem supervisão.
- A cobertura de proposições não é uniforme: a própria Câmara informa que há registros selecionados entre 1934 e 1945, proposições de determinados tipos entre 1946 e 2000 e cobertura geral das proposições tramitadas a partir de 2001. A consulta por intervalo anual também depende dos filtros e da disponibilidade do endpoint.
- Campos e endpoints podem mudar; os JSONs originais são preservados em `dados_origem` para auditoria e adaptação futura.
- O endpoint `/partidos` pode incluir partidos que têm ou já tiveram parlamentares na Câmara; a lista não deve ser interpretada como registro eleitoral atual do TSE.
- Candidaturas, votos eleitorais, resultados de eleições e bens declarados não fazem parte desta integração. São escopo futuro do adaptador do TSE.

## Validação operacional

Depois de executar os comandos no ambiente com acesso à internet e PostgreSQL, confira:

```sql
SELECT COUNT(*) FROM politicos WHERE id_camara IS NOT NULL;
SELECT COUNT(*) FROM partidos_camara;
SELECT COUNT(*) FROM mandatos_camara;
SELECT COUNT(*) FROM despesas_camara;
SELECT tipo_despesa, ano, COUNT(*), SUM(valor_liquido)
FROM despesas_camara
GROUP BY tipo_despesa, ano
ORDER BY ano DESC, tipo_despesa;
SELECT COUNT(*) FROM proposicoes_camara;
SELECT fonte, entidade, operacao, status, registros_lidos, registros_novos,
       registros_atualizados, iniciada_em, finalizada_em, mensagem
FROM data_sync_logs ORDER BY iniciada_em DESC LIMIT 20;
```

Os totais dependem do dia da coleta e dos anos selecionados; não há contagens fixas no código.
