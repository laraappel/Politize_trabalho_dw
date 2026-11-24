# Publicação: GitHub Pages e Vercel

A publicação usa dois serviços: GitHub Pages serve o frontend React/Vite como arquivos estáticos; Vercel executa a API Flask como uma função Python. O PostgreSQL precisa ser um serviço externo persistente. O Docker Compose continua sendo o ambiente de desenvolvimento local e não é substituído por esta configuração.

## GitHub Pages — frontend

O workflow [deploy-pages.yml](../.github/workflows/deploy-pages.yml) instala as dependências, compila `frontend/`, cria `404.html` para que as rotas do React Router funcionem ao abrir links diretamente e publica o artefato do Pages. Por padrão, executa após push para `main`; se o branch principal tiver outro nome, ajuste o workflow. Também pode ser iniciado manualmente em **Actions**.

Passos no GitHub:

1. Em **Settings → Pages**, selecione **GitHub Actions** como origem de publicação.
2. Em **Settings → Secrets and variables → Actions → Variables**, crie `VITE_API_URL` com a origem pública da API Vercel, por exemplo `https://<projeto-api>.vercel.app`. Informe somente a origem, sem `/api` e sem barra final.
3. Opcionalmente, configure `VITE_BASE_PATH`. Sem essa variável, o workflow usa `/<nome-do-repositório>/`, apropriado para um site de projeto. Para domínio próprio ou repositório de usuário/organização (`<usuario>.github.io`), defina `VITE_BASE_PATH` como `/`.
4. Faça push para `main` ou execute **Deploy frontend to GitHub Pages** em **Actions**. O URL final será exibido pelo job de deploy.

O frontend usa esse mesmo `VITE_API_URL` para todas as chamadas; o cliente acrescenta `/api`. A origem da API precisa aceitar CORS para o domínio do Pages.

## Vercel — dois projetos

Importe o mesmo repositório duas vezes na Vercel, criando projetos independentes:

### Frontend

- **Root Directory:** `frontend`
- Framework preset: Vite (detectado automaticamente)
- Build command: `npm run build`
- Output directory: `dist`
- Environment variable para Production e Preview: `VITE_API_URL=https://<projeto-api>.vercel.app` (sem `/api` e sem barra final)

O arquivo [frontend/vercel.json](../frontend/vercel.json) reescreve rotas da aplicação para `index.html`, permitindo recarregar ou acessar diretamente rotas como `/politicos`.

### Backend

- **Root Directory:** `backend`
- Framework preset: Flask/Python (detectado pelo `requirements.txt` e `wsgi.py`)
- O runtime Python é definido em [backend/.python-version](../backend/.python-version); a aplicação exportada por `wsgi.py` é o entrypoint Flask.
- As requisições chegam ao Flask com o caminho original. As rotas públicas da API mantêm o prefixo `/api`, por exemplo `GET https://<projeto-api>.vercel.app/api/health`; não é necessário remover ou acrescentar outro prefixo.

Configure no ambiente Vercel do backend:

| Variável | Obrigatória | Valor |
| --- | --- | --- |
| `DATABASE_URL` | Sim | URL PostgreSQL do provedor externo. Prefira a URL de pooler recomendada para serverless e SSL/TLS (`sslmode=require` quando indicado pelo provedor). |
| `FRONTEND_ORIGIN` | Sim | Origens exatas permitidas, separadas por vírgula e sem caminhos. Inclua o domínio do GitHub Pages e o domínio Vercel do frontend, por exemplo `https://<usuario>.github.io,https://<projeto-web>.vercel.app`. |
| `SECRET_KEY` | Sim | Segredo aleatório forte, diferente dos valores locais e não versionado. |
| `ADMIN_TOKEN` | Opcional | Token forte para operações editoriais de notícias. Se ausente, essas operações permanecem desabilitadas. Nunca o configure como variável `VITE_*`. |
| `CAMARA_USER_AGENT` | Recomendado | Identificação de contato para solicitações à API de dados abertos da Câmara. |

`DATABASE_URL` aceita `postgres://`, `postgresql://` e `postgresql+psycopg://`; as duas primeiras formas são normalizadas para o driver psycopg 3 incluído nas dependências. A função usa pool SQLAlchemy conservador, mas o pooler do provedor continua recomendado para limitar conexões em escalabilidade serverless. Libere a conexão de rede da Vercel no provedor de banco e mantenha TLS habilitado.

O CORS atual lê `FRONTEND_ORIGIN` como lista separada por vírgulas, não habilita credenciais e deve conter somente origens públicas confiáveis. Se usar previews Vercel, acrescente explicitamente as origens necessárias ou restrinja os previews; não use `*` em produção. Após configurar ou mudar o domínio, redeploye o backend e reconstrua o frontend para incorporar `VITE_API_URL`.

## Inicialização manual do PostgreSQL

A Vercel não executa o `entrypoint.sh` do Docker e não deve aplicar migrações em cada invocação serverless. Prepare o banco uma vez antes do primeiro deploy:

1. Crie um PostgreSQL externo persistente, com SSL e URL de conexão compatível com a Vercel.
2. No console SQL do provedor, execute `database/init/01_schema.sql` para criar o controle de migrações.
3. A partir do PowerShell na raiz deste repositório, inicie primeiro o backend local usando o `.env` normal. Depois defina temporariamente `DATABASE_URL` com a URL externa e aplique as migrações pelo container já iniciado:

   ```powershell
   docker compose up -d backend
   $env:DATABASE_URL = "<URL-POSTGRESQL-EXTERNO>"
   docker compose exec -T -e "DATABASE_URL=$env:DATABASE_URL" -e "MIGRATIONS_DIR=/database/migrations" backend flask --app wsgi migrate
   Remove-Item Env:DATABASE_URL
   ```

   O serviço de backend monta `database/migrations` em `/database/migrations`. Iniciar o container antes de definir a variável evita que o entrypoint local use a URL de produção e importe o seed de demonstração nesse banco. Não coloque a URL em arquivos versionados ou logs. Se o container ainda não foi construído, o Compose o construirá ao iniciar.
4. Opcionalmente, importe os dados de demonstração ou as fontes oficiais via CLI, apontando `DATABASE_URL` para o mesmo banco. Essas cargas não rodam automaticamente na Vercel. Para importações oficiais, consulte [API.md](API.md), [CAMARA.md](CAMARA.md) e [TSE.md](TSE.md); considere o tempo de execução e os limites de cada provedor.
5. Faça o deploy do backend e teste `GET /api/health`. Depois configure/reconstrua o frontend com o endereço público final da API.

Não use o banco de demonstração local em produção. Faça backup e teste migrações em uma base descartável antes de aplicá-las a dados importantes.

## Verificações e limitações

- `GET /api/health` verifica a conexão com PostgreSQL; o status do banco aparece como indisponível até as variáveis e migrações estarem corretas.
- A API não tem autenticação geral de usuários; considere seus dados de leitura públicos. As rotas editoriais de notícias exigem `ADMIN_TOKEN`.
- Vercel Functions são orientadas a requisições; não use o processo Flask para tarefas de longa duração, importações grandes ou agendamento contínuo. Execute cargas manualmente ou use um serviço de jobs apropriado.
- O frontend do GitHub Pages é público. Nunca compile segredos no Vite: qualquer variável `VITE_*` pode ser lida pelos visitantes.
- Para testar o modo estático localmente, rode `npm ci` e `npm run build` em `frontend/`; o Docker Compose continua indicado para desenvolvimento integrado.
