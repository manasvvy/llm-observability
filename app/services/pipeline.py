from __future__ import annotations

import time
import uuid
from typing import Any

from app.services.providers import get_provider_client


def normalize_usage(raw_usage: dict[str, Any] | None) -> dict[str, int | None]:
    usage = raw_usage or {}
    prompt_tokens = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0) or None
    completion_tokens = int(usage.get("completion_tokens") or usage.get("output_tokens") or 0) or None
    total_tokens = int(usage.get("total_tokens") or 0) or None
    if total_tokens is None and (prompt_tokens is not None or completion_tokens is not None):
        total_tokens = (prompt_tokens or 0) + (completion_tokens or 0)
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
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

    generated_request_id = request_id or str(uuid.uuid4())
    started_at = time.perf_counter()
    try:
        provider_client = get_provider_client(provider)
        response = provider_client.invoke(
            model=model,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            metadata=metadata,
        )
        usage = normalize_usage(response.get("usage"))
        observation = LLMObservation(
            request_id=generated_request_id,
            trace_id=response.get("trace_id") or generated_request_id,
            session_id=session_id,
            user_id=user_id,
            provider=provider.strip().lower(),
            model=model,
            system_prompt=system_prompt,
            prompt=prompt,
            response=response.get("content") or "",
            prompt_tokens=usage["prompt_tokens"],
            completion_tokens=usage["completion_tokens"],
            total_tokens=usage["total_tokens"],
            latency_ms=response.get("latency_ms") or round((time.perf_counter() - started_at) * 1000),
            status="success",
            finish_reason=response.get("finish_reason"),
            temperature=temperature,
            cost_usd=response.get("cost_usd"),
            metadata_json={**(metadata or {}), "provider": provider, "raw_model": model},
        )
    except Exception as exc:
        observation = LLMObservation(
            request_id=generated_request_id,
            trace_id=generated_request_id,
            session_id=session_id,
            user_id=user_id,
            provider=provider.strip().lower(),
            model=model,
            system_prompt=system_prompt,
            prompt=prompt,
            response="",
            latency_ms=round((time.perf_counter() - started_at) * 1000),
            status="error",
            error_message=str(exc),
            temperature=temperature,
            metadata_json={
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
