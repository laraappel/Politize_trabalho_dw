import os

import pytest
import requests

API_URL = os.getenv("API_URL", "http://localhost:5000")


@pytest.mark.integration
def test_health_endpoint_reports_api_and_database():
    response = requests.get(f"{API_URL}/api/health", timeout=10)

    assert response.status_code == 200
    payload = response.json()
    assert payload["api"]["status"] == "ok"
    assert payload["database"]["status"] == "ok"
    assert payload["status"] == "ok"
    assert payload["service"] == "voto-transparente-api"


@pytest.mark.integration
def test_unknown_route_returns_json_404():
    response = requests.get(f"{API_URL}/api/rota-inexistente", timeout=10)

    assert response.status_code == 404
    payload = response.json()
    assert payload["error"] == "nao_encontrado"
