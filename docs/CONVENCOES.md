# Convenções da equipe

Estas regras existem para que várias pessoas trabalhem ao mesmo tempo sem sobrescrever o código umas das outras.

## Estrutura de diretórios

| Caminho | Responsabilidade |
| --- | --- |
| `frontend/src/pages/` | Uma página por rota |
| `frontend/src/components/` | Componentes reutilizáveis |
| `frontend/src/api/` | Chamadas HTTP para o backend |
| `backend/app/routes/` | Blueprints Flask por módulo |
| `backend/app/models/` | Modelos SQLAlchemy por domínio |
| `backend/app/services/` | Regras de negócio e acesso a dados |
| `backend/app/config.py` | Configuração central |
| `database/init/` | SQL da primeira inicialização |
| `docs/` | Decisões e guias |
| `tests/` | Testes de integração compartilhados |

Não coloque CSS global novo em arquivos de página. Estilos compartilhados ficam em `frontend/src/styles/`. Componentes específicos podem usar classes novas no CSS global, com prefixo claro (`politicos-`, `noticias-`, etc.).

## Padrão de nomes

- Arquivos React: `PascalCase.jsx` (`PoliticosPage.jsx`).
- Funções e variáveis JavaScript/Python: `snake_case` no Python, `camelCase` no JavaScript.
- Blueprints: nome do módulo no plural (`politicos`, `noticias`).
- Endpoints: `/api/<modulo>` em kebab-case apenas se houver mais de uma palavra (`/api/projetos-de-lei`). Prefira um termo só: `/api/politicos`.
- Tabelas SQL: snake_case no plural (`politicos`, `mandatos`).
- Branches Git: `tipo/modulo-resumo`.

Exemplos de branch:

- `feat/frontend-busca-politicos`
- `feat/backend-perfil-politico`
- `docs/convenio-git`
- `fix/backend-health-db`

## Como criar uma nova rota no frontend

1. Crie a página em `frontend/src/pages/NomePage.jsx`.
2. Registre a rota em `frontend/src/App.jsx`.
3. Se a página deve aparecer no menu, adicione o item em `frontend/src/components/layout/Header.jsx`.
4. Chamadas de API entram em `frontend/src/api/`, nunca dentro do JSX misturadas com HTML.

Rotas já reservadas:

- `/`
- `/transparencia`
- `/politicos`
- `/politicos/:id`
- `/noticias`
- `/colinha`
- `/sobre`

## Como criar um endpoint no backend

1. Crie `backend/app/routes/<modulo>.py` com um `Blueprint`.
2. Registre o blueprint em `backend/app/routes/__init__.py` com `url_prefix="/api"`.
3. Coloque consultas e regras em `backend/app/services/<modulo>.py`.
4. Coloque modelos em `backend/app/models/<entidade>.py`.
5. Não acesse `db.session` diretamente nas rotas, salvo endpoints triviais como saúde.

Exemplo mínimo:

```python
from flask import Blueprint, jsonify

politicos_bp = Blueprint("politicos", __name__)

@politicos_bp.get("/politicos")
def listar_politicos():
    return jsonify({"items": []})
```

Depois, em `register_blueprints`:

```python
from app.routes.politicos import politicos_bp
app.register_blueprint(politicos_bp, url_prefix="/api")
```

## Como acessar o banco de dados

Pelo Docker:

```bash
docker compose exec db psql -U voto -d voto_transparente
```

A senha é a do arquivo `.env` local (`POSTGRES_PASSWORD`). O host interno é `db`; na máquina host use `localhost` e a porta `POSTGRES_PORT`.

Scripts SQL novos:

1. Crie `database/migrations/00X_descricao.sql` (ou continue a sequência em `database/init/` apenas se o volume ainda não existe).
2. Documente a mudança no PR.
3. Nunca edite um script já aplicado no volume compartilhado da equipe.

## Variáveis de ambiente

1. Copie `.env.example` para `.env`.
2. Altere senhas e `SECRET_KEY` no seu computador.
3. **Não** commite `.env`.
4. Se precisar de uma variável nova, adicione-a em `.env.example`, no `docker-compose.yml` e em `backend/app/config.py` (ou no frontend via `VITE_`).

No frontend, apenas variáveis com prefixo `VITE_` chegam ao navegador.

## Git e branches

- `main` permanece estável e executável com Docker.
- Cada pessoa trabalha em uma branch a partir de `main`.
- Um pull request por módulo ou correção.
- Commits pequenos e descritivos, em português ou inglês, mas consistentes no PR.

Fluxo:

```bash
git checkout main
git pull
git checkout -b feat/frontend-filtros-politicos
# ...alterações...
git add arquivos-do-seu-modulo
git commit -m "Adiciona filtros da busca de políticos"
git push -u origin feat/frontend-filtros-politicos
```

## Como evitar conflitos entre módulos

1. **Dono do arquivo:** se dois módulos precisam do mesmo arquivo (`App.jsx`, `Header.jsx`, `routes/__init__.py`), faça a alteração mínima e avise no grupo. Prefira PRs curtos nesses arquivos.
2. **Não reformate o projeto inteiro** em um PR de funcionalidade.
3. **Não misture frontend e backend** no mesmo PR, salvo quando o contrato da API exigir os dois lados.
4. **Contrato primeiro:** defina o JSON da API em `docs/` ou no próprio PR antes de ambos os lados implementarem em paralelo.
5. **Namespaces:** CSS, tabelas, blueprints e pastas devem usar o nome do módulo.
6. **Atualize `main` com frequência** (`git pull`) para reduzir merges grandes.
7. Se o Git reportar conflito, resolva apenas as linhas do seu módulo e preserve o trabalho da outra pessoa.

## Comunicação frontend e backend

- Base da API no navegador: `VITE_API_URL` (padrão `http://localhost:5000`).
- Prefixo: `/api`.
- Lista paginada futura: `{ "items": [], "total": 0, "page": 1 }`.
- Recurso único: objeto no raiz, sem envelope extra, salvo quando houver metadados.

Quem cria um endpoint atualiza este documento se o padrão mudar.
