from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.observations import LLMObservation
from app.schemas import (
    LLMCallRequest,
    LLMObservationCreate,
    LLMObservationRead,
    ObservationSummary,
    ProviderStatus,
)
from app.services.pipeline import ingest_llm_call
from app.services.providers import get_supported_providers

router = APIRouter(prefix="/api/v1", tags=["observations"])


@router.post("/observations", response_model=LLMObservationRead, status_code=status.HTTP_201_CREATED)
def create_observation(payload: LLMObservationCreate, db: Session = Depends(get_db)) -> LLMObservation:
    observation = LLMObservation(**payload.model_dump())
    db.add(observation)
    db.commit()
    db.refresh(observation)
    return observation


@router.post("/observations/ingest", response_model=LLMObservationRead, status_code=status.HTTP_201_CREATED)
def ingest_observation(payload: LLMCallRequest, db: Session = Depends(get_db)) -> LLMObservation:
    return ingest_llm_call(
        db=db,
        provider=payload.provider,
        model=payload.model,
        prompt=payload.prompt,
        system_prompt=payload.system_prompt,
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
        metadata=payload.metadata,
        request_id=payload.request_id,
        session_id=payload.session_id,
        user_id=payload.user_id,
    )


@router.get("/observations", response_model=list[LLMObservationRead])
def list_observations(
    provider: str | None = Query(default=None),
    model: str | None = Query(default=None),
    status: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
    session_id: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[LLMObservation]:
    query = db.query(LLMObservation)

    if provider:
        query = query.filter(LLMObservation.provider == provider)
    if model:
        query = query.filter(LLMObservation.model == model)
    if status:
        query = query.filter(LLMObservation.status == status)
    if user_id:
        query = query.filter(LLMObservation.user_id == user_id)
    if session_id:
        query = query.filter(LLMObservation.session_id == session_id)

    return query.order_by(LLMObservation.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/observations/{observation_id}", response_model=LLMObservationRead)
def get_observation(observation_id: int, db: Session = Depends(get_db)) -> LLMObservation:
    observation = db.query(LLMObservation).filter(LLMObservation.id == observation_id).first()
    if observation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Observation not found")
    return observation


@router.get("/observations/summary", response_model=ObservationSummary)
def observation_summary(db: Session = Depends(get_db)) -> ObservationSummary:
    total = db.query(func.count(LLMObservation.id)).scalar() or 0
    success_count = (
        db.query(func.count(LLMObservation.id))
        .filter(LLMObservation.status == "success")
        .scalar()
        or 0
    )
    avg_latency = db.query(func.avg(LLMObservation.latency_ms)).scalar() or 0

    provider_breakdown = {
        row.provider: row.count
        for row in db.query(LLMObservation.provider, func.count(LLMObservation.id).label("count"))
        .group_by(LLMObservation.provider)
        .all()
    }
    status_breakdown = {
        row.status: row.count
        for row in db.query(LLMObservation.status, func.count(LLMObservation.id).label("count"))
        .group_by(LLMObservation.status)
        .all()
    }

    return ObservationSummary(
        total_observations=total,
        success_rate=(success_count / total * 100) if total else 0.0,
        avg_latency_ms=float(avg_latency),
        provider_breakdown=provider_breakdown,
        status_breakdown=status_breakdown,
    )


@router.get("/providers", response_model=list[ProviderStatus])
def list_providers() -> list[ProviderStatus]:
    return get_supported_providers()
