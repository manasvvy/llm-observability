# llm-observability

A lightweight FastAPI service for recording and inspecting LLM requests and responses.

## Features

- FastAPI-based API
- SQLite-backed storage with SQLAlchemy
- Endpoints for creating, listing, and retrieving LLM observations
- Request logging middleware
- Ready for local development with `uvicorn`

## Quick start

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

If you prefer to install from the project metadata:

```bash
pip install -e .
```

3. Start the app:

```bash
python main.py
```

4. Visit:

- `http://localhost:8000/health`
- `http://localhost:8000/api/v1/observations`

## API examples

### Create an observation

```bash
curl -X POST http://localhost:8000/api/v1/observations \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "anthropic",
    "model": "claude-3-5-sonnet-20241022",
    "prompt": "Summarize this document.",
    "response": "This document describes a lightweight observability system.",
    "latency_ms": 430,
    "status": "success",
    "metadata": {"temperature": 0.2, "tokens": 124}
  }'
```

### List observations

```bash
curl http://localhost:8000/api/v1/observations
```

## Project structure

```text
app/
├── db.py
├── main.py
├── schemas.py
├── models/
│   ├── __init__.py
│   └── observations.py
├── routers/
│   ├── __init__.py
│   └── observations.py
├── middleware/
│   └── logging.py
└── __init__.py
```
