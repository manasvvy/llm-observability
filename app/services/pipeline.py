from __future__ import annotations

import os
import time
import uuid
from typing import Any

import httpx

from app.services.providers import get_provider_client


def normalize_usage(raw_usage: dict[str, Any] | None) -> dict[str, int | None]:
    usage = raw_usage or {}
    return {
        "prompt_tokens": int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0) or None,
        "completion_tokens": int(usage.get("completion_tokens") or usage.get("output_tokens") or 0) or None,
        "total_tokens": int(usage.get("total_tokens") or 0) or None,
    }


def ingest_llm_call(
    db,
    *,
    provider: str,
    model: str,
    prompt: str,
    system_prompt: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    metadata: dict[str, Any] | None = None,
    request_id: str | None = None,
    session_id: str | None = None,
    user_id: str | None = None,
):
    from app.models.observations import LLMObservation

    try:
        provider_client = get_provider_client(provider)
        started_at = time.perf_counter()
        response = provider_client.invoke(
            model=model,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            metadata=metadata,
        )
        elapsed_ms = round((time.perf_counter() - started_at) * 1000)

        normalized_usage = normalize_usage(response.get("usage"))
        observation = LLMObservation(
            request_id=request_id or str(uuid.uuid4()),
            trace_id=response.get("trace_id") or request_id or str(uuid.uuid4()),
            session_id=session_id,
            user_id=user_id,
            provider=provider,
            model=model,
            system_prompt=system_prompt,
            prompt=prompt,
            response=response.get("content") or "",
            prompt_tokens=normalized_usage["prompt_tokens"],
            completion_tokens=normalized_usage["completion_tokens"],
            total_tokens=normalized_usage["total_tokens"],
            latency_ms=response.get("latency_ms") or elapsed_ms,
            status="success",
            finish_reason=response.get("finish_reason"),
            temperature=temperature,
            cost_usd=response.get("cost_usd"),
            metadata={
                **(metadata or {}),
                "provider_response": response.get("provider_response", {}),
                "provider": provider,
                "raw_model": model,
            },
        )
    except Exception as exc:
        observation = LLMObservation(
            request_id=request_id or str(uuid.uuid4()),
            trace_id=request_id or str(uuid.uuid4()),
            session_id=session_id,
            user_id=user_id,
            provider=provider,
            model=model,
            system_prompt=system_prompt,
            prompt=prompt,
            response="",
            latency_ms=0,
            status="error",
            error_message=str(exc),
            temperature=temperature,
            metadata={
                **(metadata or {}),
                "provider": provider,
                "raw_model": model,
                "exception_type": type(exc).__name__,
            },
        )

    db.add(observation)
    db.commit()
    db.refresh(observation)
    return observation
