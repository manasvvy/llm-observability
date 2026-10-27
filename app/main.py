from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.db import init_db
from app.routers import router as root_router
from app.routers.observations import router as observations_router
from app.middleware.logging import logging_middleware

load_dotenv()


app = FastAPI(
    title="LLM Observability Layer",
    version="0.1.0",
    description="A lightweight observability layer for tracking LLM calls and responses.",
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
