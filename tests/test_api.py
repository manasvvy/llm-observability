from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models.observations import LLMObservation  # noqa: F401


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "llm-observability"


def test_mock_chat_endpoint(client):
    response = client.post(
        "/llm/chat",
        json={"provider": "mock", "model": "demo-model", "prompt": "What is AI observability?", "max_tokens": 64},
    )
    assert response.status_code == 200
    assert response.json()["provider"] == "mock"
    assert response.json()["reply"]


def test_create_get_and_filter_observation(client):
    created = client.post(
        "/api/v1/observations",
        json={
            "provider": "mock",
            "model": "demo-model",
            "prompt": "hello",
            "response": "world",
            "latency_ms": 25,
            "metadata": {"tag": "test"},
        },
    )
    assert created.status_code == 201
    item = created.json()
    assert item["metadata"] == {"tag": "test"}
    assert client.get(f"/api/v1/observations/{item['id']}").json() == item
    assert len(client.get("/api/v1/observations?provider=mock").json()) == 1
    assert client.get("/api/v1/observations?provider=anthropic").json() == []


def test_ingest_mock_call_is_persisted(client):
    response = client.post(
        "/api/v1/observations/ingest",
        json={"provider": "mock", "model": "demo-model", "prompt": "hello", "metadata": {"source": "test"}},
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["response"]
    assert payload["total_tokens"] == payload["prompt_tokens"] + payload["completion_tokens"]


def test_summary_and_providers(client):
    client.post(
        "/api/v1/observations",
        json={"provider": "mock", "model": "demo", "prompt": "p", "response": "r", "latency_ms": 20},
    )
    client.post(
        "/api/v1/observations",
        json={"provider": "openai", "model": "demo", "prompt": "p", "response": "", "status": "error", "latency_ms": 40},
    )
    summary = client.get("/api/v1/observations/summary").json()
    assert summary["total_observations"] == 2
    assert summary["success_rate"] == 50.0
    assert summary["avg_latency_ms"] == 30.0
    assert summary["provider_breakdown"] == {"mock": 1, "openai": 1}
    assert summary["status_breakdown"] == {"success": 1, "error": 1}
    providers = client.get("/api/v1/providers")
    assert providers.status_code == 200
    assert {provider["name"] for provider in providers.json()} >= {"mock", "openai", "anthropic", "ollama"}


def test_missing_observation_returns_404(client):
    response = client.get("/api/v1/observations/999")
    assert response.status_code == 404


def test_invalid_pagination_is_rejected(client):
    assert client.get("/api/v1/observations?limit=0").status_code == 422
