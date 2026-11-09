# LLM Observability & Guardrails Layer

A small FastAPI service for sending requests to supported LLM providers and recording LLM-call observations. It captures provider, model, prompt/response, latency, token usage, status, and metadata so you can inspect calls and view basic summary metrics.

**Live demo:** https://llm-observability-4ecn.onrender.com  
**Interactive API docs:** https://llm-observability-4ecn.onrender.com/docs

> This is a student project/demo, not a production-ready guardrails product. The current implementation does not evaluate confidence, block unsafe outputs, or enforce guardrail policies. The API includes a mock provider for no-key demos; real provider calls require the relevant configuration. The deployed demo uses SQLite on Render's free service, so stored data may not persist across restarts or redeploys.

## Features

- FastAPI endpoints with interactive Swagger documentation
- Mock provider for demos without API keys
- Provider adapters for OpenAI-compatible APIs, Anthropic, and Ollama
- Observation creation and LLM-call ingestion endpoints
- Observation listing with provider, model, status, user, and session filters
- Summary metrics for request count, success rate, average latency, and provider/status breakdowns
- SQLAlchemy persistence, using SQLite by default and optionally PostgreSQL via `DATABASE_URL`
- Docker-based deployment configuration for Render

## Run locally

Requires Python 3.12 or newer.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Then open:

- http://localhost:8000/docs — interactive API docs
- http://localhost:8000/health — health check

The default database is `sqlite:///./llm_observability.db`. To use PostgreSQL, set `DATABASE_URL` to your SQLAlchemy-compatible connection URL before starting the app. Do not commit credentials or API keys.

## Try the mock provider

The mock provider works without an API key:

```bash
curl -X POST https://llm-observability-4ecn.onrender.com/llm/chat \
  -H "Content-Type: application/json" \
  -d '{"provider":"mock","model":"demo-model","prompt":"What is LLM observability?"}'
```

To persist a call as an observation and receive an observation record, use the ingestion endpoint:

```bash
curl -X POST https://llm-observability-4ecn.onrender.com/api/v1/observations/ingest \
  -H "Content-Type: application/json" \
  -d '{"provider":"mock","model":"demo-model","prompt":"Hello"}'
```

## Main endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Health check |
| `POST` | `/llm/chat` | Send a prompt to a configured provider |
| `POST` | `/api/v1/observations` | Create an observation record |
| `POST` | `/api/v1/observations/ingest` | Run a provider call and save its observation |
| `GET` | `/api/v1/observations` | List observations; supports filters and pagination |
| `GET` | `/api/v1/observations/{id}` | Retrieve one observation |
| `GET` | `/api/v1/observations/summary` | Get aggregate metrics |
| `GET` | `/api/v1/providers` | List supported providers and configuration status |

See `/docs` for request schemas and examples.

## Provider configuration

- `mock`: no configuration required.
- `openai`: set `OPENAI_API_KEY`; optionally set `OPENAI_BASE_URL` for an OpenAI-compatible API.
- `anthropic`: set `ANTHROPIC_API_KEY`; optionally set `ANTHROPIC_BASE_URL`.
- `ollama`: set `OLLAMA_BASE_URL` to a reachable Ollama server. An Ollama instance running only on your own computer is not automatically reachable from the Render deployment.

Set secrets in your hosting provider's environment settings, not in source code or committed files. Provider calls may incur charges according to the provider's pricing.

## Deployment

The app is deployed as a free Render web service using the repository's Dockerfile and `render.yaml`. The demo currently defaults to SQLite. Render's free service can spin down after inactivity, so the first request may take a little while to respond. SQLite data on the free service should be treated as temporary. For data you need to keep, configure a persistent database such as PostgreSQL.

## Tests

Run the test suite with:

```bash
pytest
```

## Built with

Python · FastAPI · SQLAlchemy · SQLite/PostgreSQL · Docker · Render

## License

No license has been specified yet. Ask the repository owner before reusing or redistributing this project.
