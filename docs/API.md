# Contrato da API

Base local no navegador: `http://localhost:5001/api`. O frontend usa `VITE_API_URL` como origem e acrescenta `/api` nas chamadas. Dentro do container o Flask escuta a porta `5000`. O backend permite as origens configuradas em `FRONTEND_ORIGIN` (lista separada por vírgulas).

## Formatos comuns

- Datas: ISO 8601 (`AAAA-MM-DD` ou data/hora ISO).
- Valores financeiros: string decimal com duas casas ou `null`; `null` significa não informado, não zero.
- Listas paginadas: `{ "items": [], "total": 0, "page": 1, "per_page": 10, "pages": 0 }`. `per_page` tem máximo 50.
- Erros: `{ "error": "codigo_estavel", "message": "mensagem" }`.
- Campos de origem: `origem_dados`, `demonstracao` e `fonte` (`{ "nome", "url" }` ou `null`).

## Rotas

| Método e rota | Parâmetros / resposta |
| --- | --- |
| `GET /health` | Estado da API e do banco; retorna 503 quando o banco está indisponível. |
| `GET /politicos` | Filtros `q`, `cargo`, `partido`, `uf`, `page`, `per_page`; lista resumida paginada. |
| `GET /politicos/filtros` | Opções `cargos`, `partidos`, `ufs`. |
| `GET /politicos/<id>` | Perfil e relações `mandatos`, `projetos`, `votacoes`, `despesas`, `resumo_financeiro`. |
| `GET /politicos/<id>/mandatos` | Mandatos paginados. |
| `GET /politicos/<id>/projetos` | Projetos paginados. |
| `GET /politicos/<id>/votacoes` | Votações paginadas. |
| `GET /politicos/<id>/despesas` | Despesas paginadas; aceita `categoria`, `de`, `ate`. |
| `GET /transparencia` | Contagens e resumo agregado do cadastro ativo. |
| `GET /transparencia/despesas` | Lista paginada; filtros `categoria`, `uf`, `de`, `ate`. |
| `GET /transparencia/filtros` | Opções `categorias` e `ufs`. |
| `GET /noticias` | Filtros `politico`, `veiculo`, `assunto`, `natureza`, `de`, `ate`, `ordem` (`recentes` ou `antigas`), `page`, `per_page`. Exibe apenas associações confirmadas. |
| `GET /noticias/<id>` | Detalhe público, evidências e atualizações. |
| `GET /noticias/filtros` | Opções disponíveis para notícias públicas. |
| `GET /politicos/<id>/noticias` | Notícias confirmadas relacionadas ao perfil; mesmos filtros de notícia. |
| `GET /veiculos` | Fontes monitoradas e base declarada de autorização. |

Datas `de` e `ate` são inclusivas e devem estar no formato `AAAA-MM-DD`. Parâmetros inválidos retornam HTTP 400; recursos ausentes retornam 404.

## Operações editoriais de notícias

Requerem `X-Admin-Token` igual a `ADMIN_TOKEN`. Se `ADMIN_TOKEN` estiver vazio, ficam desabilitadas:

- `GET /noticias/revisao`: associações pendentes.
- `POST /noticias/<id>/politicos/<politico_id>/revisao`: corpo `{ "decisao": "confirmar|rejeitar", "revisado_por": "..." }`.
- `PATCH /noticias/<id>/natureza`: corpo `{ "natureza": "..." }`.
- `POST /noticias/<id>/atualizacoes`: corpo com `tipo`, `descricao` e, opcionalmente, `url_referencia`, `noticia_relacionada_id`, `criado_por`.

## Importação

Importação é uma operação de linha de comando, não uma rota HTTP:

```powershell
docker compose exec backend flask --app wsgi importar-dados --arquivo /database/seeds/demonstracao.json
```

O formato e as regras estão em [database/README.md](../database/README.md). O pacote é idempotente para as chaves naturais existentes. Projetos com o mesmo identificador em mais de um político são rejeitados até que a coautoria seja implementada.

## Rotas não disponíveis

O cadastro de candidaturas e outras classes eleitorais em arquivos de modelo ainda não tem migrações nem rotas registradas. Não são parte deste contrato.
