# Testes

Os testes de integração assumem que a stack Docker está em execução e usa PostgreSQL migrado.

Execute todos os testes no container backend:

```powershell
docker compose exec -T backend pytest -c /app/pytest.ini /tests -q
```

O `-c /app/pytest.ini` carrega configuração e caminho de importação Python do container; sem ele, o pytest iniciado apontando para `/tests` não encontra o pacote `app`.

Para executar somente os testes HTTP a partir do host, instale `pytest` e `requests` e configure:

```powershell
$env:API_URL = "http://localhost:5001"
pytest tests/integration/test_health.py -q
```

`tests/unit/` cobre regras sem banco. Os testes de integração de domínio e notícias usam dados sintéticos e limpam os registros criados.
