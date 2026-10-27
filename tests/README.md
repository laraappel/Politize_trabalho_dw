# Testes

Nesta etapa existem testes de integração da API, em `tests/integration/`.

Eles assumem que o backend já está no ar (`docker compose up`).

Na máquina host:

```bash
pip install requests pytest
pytest tests/integration/test_health.py
```

Variável opcional:

```bash
set API_URL=http://localhost:5000
```
