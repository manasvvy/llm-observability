from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.observations import LLMObservation
from app.schemas import LLMObservationCreate, LLMObservationRead

router = APIRouter(prefix="/api/v1", tags=["observations"])


@router.post("/observations", response_model=LLMObservationRead, status_code=status.HTTP_201_CREATED)
def create_observation(payload: LLMObservationCreate, db: Session = Depends(get_db)) -> LLMObservation:
    observation = LLMObservation(**payload.model_dump())
    db.add(observation)
    db.commit()
    db.refresh(observation)
    return observation


@router.get("/observations", response_model=list[LLMObservationRead])
def list_observations(
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> list[LLMObservation]:
    return (
        db.query(LLMObservation)
        .order_by(LLMObservation.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/observations/{observation_id}", response_model=LLMObservationRead)
def get_observation(observation_id: int, db: Session = Depends(get_db)) -> LLMObservation:
    observation = db.query(LLMObservation).filter(LLMObservation.id == observation_id).first()
    if observation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Observation not found")
    return observation
