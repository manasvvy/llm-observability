from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "llm-observability"


def test_mock_chat_endpoint():
    response = client.post(
        "/llm/chat",
        json={
            "provider": "mock",
            "model": "demo-model",
            "prompt": "What is AI observability?",
            "max_tokens": 64,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "mock"
    assert "reply" in payload
