from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LLMObservationCreate(BaseModel):
    provider: str
    model: str
    prompt: str
    response: str
    latency_ms: int = 0
    status: str = "success"
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMObservationRead(LLMObservationCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
