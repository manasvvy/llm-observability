from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def root() -> dict[str, Any]:
    return {
        "service": "llm-observability",
        "status": "ok",
        "version": "0.2.0",
        "docs": "/docs",
    }
