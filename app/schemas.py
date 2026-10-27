from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LLMObservationCreate(BaseModel):
    request_id: str | None = None
    trace_id: str | None = None
    session_id: str | None = None
    user_id: str | None = None
    provider: str
    model: str
    system_prompt: str | None = None
    prompt: str
    response: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    latency_ms: int = 0
    status: str = "success"
    finish_reason: str | None = None
    error_message: str | None = None
    temperature: float | None = None
    cost_usd: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMCallRequest(BaseModel):
    provider: str
    model: str
    prompt: str
    system_prompt: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    request_id: str | None = None
    session_id: str | None = None
    user_id: str | None = None


class LLMObservationRead(LLMObservationCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class ObservationSummary(BaseModel):
    total_observations: int
    success_rate: float
    avg_latency_ms: float
    provider_breakdown: dict[str, int]
    status_breakdown: dict[str, int]


class ProviderStatus(BaseModel):
    name: str
    configured: bool
    base_url: str | None = None
    description: str
