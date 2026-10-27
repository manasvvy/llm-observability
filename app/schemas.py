from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LLMObservationCreate(BaseModel):
    request_id: str | None = None
    session_id: str | None = None
    user_id: str | None = None
    provider: str
    model: str
    prompt: str
    response: str
    latency_ms: int = 0
    status: str = "success"
    error_message: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    temperature: float | None = None
    cost_usd: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMObservationUpdate(BaseModel):
    provider: str | None = None
    model: str | None = None
    prompt: str | None = None
    response: str | None = None
    latency_ms: int | None = None
    status: str | None = None
    error_message: str | None = None
    metadata: dict[str, Any] | None = None


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
