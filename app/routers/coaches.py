from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/coaches", tags=["Coaches"])


@router.get("/", response_model=List[schemas.CoachOut])
def list_coaches(
    skip: int = 0,
    limit: int = 100,
    club_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Coach)
    if club_id:
        q = q.filter(models.Coach.club_id == club_id)
    return q.order_by(models.Coach.last_name).offset(skip).limit(limit).all()


@router.post("/", response_model=schemas.CoachOut, status_code=201)
def create_coach(payload: schemas.CoachCreate, db: Session = Depends(get_db)):
    if db.query(models.Coach).filter(
        models.Coach.licence_number == payload.licence_number
    ).first():
        raise HTTPException(400, detail="Coach licence number already exists")
    coach = models.Coach(**payload.model_dump())
    db.add(coach)
    db.commit()
    db.refresh(coach)
    return coach


@router.get("/{coach_id}", response_model=schemas.CoachOut)
def get_coach(coach_id: int, db: Session = Depends(get_db)):
    coach = db.query(models.Coach).filter(models.Coach.id == coach_id).first()
    if not coach:
        raise HTTPException(404, detail="Coach not found")
    return coach


@router.patch("/{coach_id}", response_model=schemas.CoachOut)
def update_coach(coach_id: int, payload: schemas.CoachUpdate, db: Session = Depends(get_db)):
    coach = db.query(models.Coach).filter(models.Coach.id == coach_id).first()
    if not coach:
        raise HTTPException(404, detail="Coach not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(coach, k, v)
    db.commit()
    db.refresh(coach)
    return coach


@router.delete("/{coach_id}", status_code=204)
def delete_coach(coach_id: int, db: Session = Depends(get_db)):
    coach = db.query(models.Coach).filter(models.Coach.id == coach_id).first()
    if not coach:
        raise HTTPException(404, detail="Coach not found")
    db.delete(coach)
    db.commit()
