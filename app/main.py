from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db
from app.middleware.logging import logging_middleware
from app.routers import router as root_router
from app.routers.observations import router as observations_router

app = FastAPI(
    title="LLM Observability Pipeline",
    version="0.3.0",
    description="A real multi-model observability platform for capturing LLM calls across providers and analyzing outcomes.",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(logging_middleware)

app.include_router(root_router)
app.include_router(observations_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.on_event("startup")
def startup() -> None:
    init_db()
