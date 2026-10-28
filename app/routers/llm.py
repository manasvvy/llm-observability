from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.providers import get_provider_client

router = APIRouter()


class LLMRequest(BaseModel):
    provider: str = "mock"
    model: str = "mock-model"
    prompt: str
    system_prompt: str | None = None
    max_tokens: int = 256
    temperature: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    session_id: str | None = None
    user_id: str | None = None


@router.post("/chat")
def chat(request: LLMRequest):
    try:
        provider_client = get_provider_client(request.provider)
        response = provider_client.invoke(
            model=request.model,
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            metadata=request.metadata,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive fallback
        raise HTTPException(status_code=500, detail=f"LLM request failed: {exc}") from exc

    result = {
        "provider": request.provider,
        "model": request.model,
        "reply": response.get("content", ""),
        "latency_ms": response.get("latency_ms", 0),
        "usage": response.get("usage", {}),
        "finish_reason": response.get("finish_reason"),
        "cost_usd": response.get("cost_usd"),
        "metadata": {
            **(request.metadata or {}),
            "provider_response": response.get("provider_response", {}),
        },
    }

    return result
