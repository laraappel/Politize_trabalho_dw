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

## Notícias

- `tests/unit/`: regras puras (associação, classificação, RSS). Rode com `PYTHONPATH=backend pytest tests/unit`.
- `tests/integration/test_noticias_db.py`: fluxo completo contra um PostgreSQL migrado (`DATABASE_URL`). Usa apenas dados sintéticos e limpa o que cria.
