from __future__ import annotations

from typing import Any

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def root() -> dict[str, Any]:
    return {
        "service": "llm-observability",
        "status": "ok",
        "version": "0.3.0",
        "architecture": "multi-model observability pipeline",
        "docs": "/docs",
    }
