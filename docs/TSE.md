# Integração com o TSE

## Fonte e cobertura

A integração utiliza os arquivos ZIP de candidaturas do Portal de Dados Abertos do TSE, com licença Creative Commons Attribution (CC BY):

- 2022: https://dadosabertos.tse.jus.br/dataset/candidatos-2022 e `consulta_cand_2022.zip`.
- 2024: https://dadosabertos.tse.jus.br/dataset/candidatos-2024 e `consulta_cand_2024.zip`.

São importadas somente candidaturas cuja situação de totalização publicada pelo TSE começa por `ELEITO`, para Presidente, Governador, Senador, Deputado Federal, Deputado Estadual/Distrital, Prefeito e Vereador. A situação textual original e o ano eleitoral são mantidos. Isso significa que os dados representam o resultado daquela eleição; não são afirmação de que o mandato ainda está em exercício.

Os ZIPs são lidos sem extração para o disco, com codificação Latin-1 e delimitador CSV `;`. Os identificadores de candidato do TSE são preservados na tabela de cargos. Quando há CPF na fonte, ele é usado apenas para gerar uma chave SHA-256 pseudonimizada e unificar o mesmo indivíduo; o CPF em claro não é persistido. Sem CPF, o identificador do candidato/eleição mantém os registros separados. Cadastros existentes só são reutilizados por correspondência exata e única de nome e UF.

A integração não carrega votos nominais: o conjunto de candidaturas não é a fonte oficial de votos. O campo permanece ausente, em vez de ser inventado. Para votação nominal, será necessário integrar separadamente os arquivos de resultados do TSE.

## Importar e atualizar

Execute no backend com acesso à internet e após aplicar as migrações (em especial `011_cargos_eletivos_oficiais.sql` e `012_sigla_partido_candidatura.sql`):

```powershell
docker compose exec backend flask --app wsgi sincronizar-tse
docker compose exec backend flask --app wsgi sincronizar-tse --anos 2022
```

A carga padrão sincroniza 2022 e 2024 e é idempotente por identificador TSE/ano. A importação não roda automaticamente ao iniciar a aplicação, para não baixar arquivos grandes durante a inicialização.

## Consulta

- `GET /api/cargos-eletivos?cargo=Prefeito&ano=2024&uf=SC`
- `GET /api/cargos-eletivos?cargo=Deputado Federal&ano=2022`
- `GET /api/politicos/<id>/candidaturas`
- `GET /api/cargos-eletivos/filtros`

A página de pesquisa oferece cargo, partido, UF e ano. As tarjetas e os perfis mostram o ano eleitoral e a situação oficial. A fonte e o link do TSE acompanham os registros.

## Limitações

- Anos disponíveis atualmente: 2022 e 2024. O CLI rejeita anos sem arquivo configurado.
- Um candidato sem CPF pode permanecer em perfis diferentes em eleições distintas; não se associa por nome aproximado.
- Resultados podem ser atualizados pelo TSE. Reexecute o comando para sincronizar a versão mais recente publicada.
- A API não identifica automaticamente afastamentos, cassações ou ocupantes atuais com base no resultado eleitoral histórico.
