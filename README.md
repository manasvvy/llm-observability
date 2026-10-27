# llm-observability

A production-ready FastAPI service for capturing and inspecting LLM calls, model performance, usage patterns, and operational health.

## Why this project matters

LLM applications are hard to debug because requests are often opaque: the prompt, model, latency, token usage, output quality, and environment all matter. This project gives you a practical observability layer so you can track the full lifecycle of each model call and detect regressions quickly.

## Features

- FastAPI API with interactive Swagger docs
- SQLite-backed persistence with SQLAlchemy
- Structured observation model for LLM calls
- Request logging middleware with timing output
- Summary endpoint for application health and usage insights
- Filterable listing for provider, model, status, session, and user context
- Ready for local development and extension

## Quick start

### 1) Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Run the application

```bash
python main.py
```

Then visit:

- http://localhost:8000/
- http://localhost:8000/health
- http://localhost:8000/docs

## API overview

### Create an observation

```bash
curl -X POST http://localhost:8000/api/v1/observations \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "req_123",
    "session_id": "session_abc",
    "user_id": "user_42",
    "provider": "anthropic",
    "model": "claude-3-5-sonnet-20241022",
    "prompt": "Summarize this document in 3 bullet points.",
    "response": "- Uses a lightweight observability layer\n- Captures latency and token metrics\n- Helps debug LLM quality regressions",
    "latency_ms": 540,
    "status": "success",
    "input_tokens": 120,
    "output_tokens": 40,
    "total_tokens": 160,
    "temperature": 0.2,
    "cost_usd": 0.0042,
    "metadata": {
      "temperature": 0.2,
      "top_p": 1.0,
      "agent": "summarizer"
    }
  }'
```

### List observations with filters

```bash
curl "http://localhost:8000/api/v1/observations?provider=anthropic&status=success&limit=20"
```

### Summary metrics

```bash
curl http://localhost:8000/api/v1/observations/summary
```

## Example response

```json
{
  "total_observations": 42,
  "success_rate": 96.0,
  "avg_latency_ms": 643.5,
  "provider_breakdown": {
    "anthropic": 31,
    "openai": 11
  },
  "status_breakdown": {
    "success": 40,
    "error": 2
  }
}
```

## Project structure

```text
app/
├── __init__.py
├── db.py
├── main.py
├── schemas.py
├── middleware/
│   └── logging.py
├── models/
│   ├── __init__.py
│   └── observations.py
├── routers/
│   ├── __init__.py
│   └── observations.py
├── utils/
│   └── (optional future extensions)
└── services/
    └── (optional future integrations)
```

## Recommended next upgrades

- Add authentication and API keys
- Add dashboard UI for visualization
- Add Prometheus metrics export
- Add OpenTelemetry tracing
- Add support for multi-provider backends and async DB access
- Add test suite with pytest

## License

This project is intentionally lightweight and easy to extend for your own LLM monitoring workflows.
