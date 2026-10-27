from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def root() -> dict[str, str]:
    return {"service": "llm-observability", "status": "ok"}
