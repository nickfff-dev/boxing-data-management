from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/clubs", tags=["Clubs"])


def get_club_or_404(club_id: int, db: Session) -> models.Club:
    c = db.query(models.Club).filter(models.Club.id == club_id).first()
    if not c:
        raise HTTPException(404, detail=f"Club {club_id} not found")
    return c


@router.get("/", response_model=List[schemas.ClubOut])
def list_clubs(
    skip: int = 0,
    limit: int = 100,
    county: Optional[str] = None,
    type: Optional[models.ClubTypeEnum] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Club)
    if county:
        q = q.filter(models.Club.county.ilike(f"%{county}%"))
    if type:
        q = q.filter(models.Club.type == type)
    return q.order_by(models.Club.name).offset(skip).limit(limit).all()


@router.post("/", response_model=schemas.ClubOut, status_code=201)
def create_club(payload: schemas.ClubCreate, db: Session = Depends(get_db)):
    if db.query(models.Club).filter(
        models.Club.bfk_affiliation_no == payload.bfk_affiliation_no
    ).first():
        raise HTTPException(400, detail="Affiliation number already registered")
    club = models.Club(**payload.model_dump())
    db.add(club)
    db.commit()
    db.refresh(club)
    return club


@router.get("/{club_id}", response_model=schemas.ClubDetail)
def get_club(club_id: int, db: Session = Depends(get_db)):
    club = (
        db.query(models.Club)
        .options(joinedload(models.Club.coaches))
        .filter(models.Club.id == club_id)
        .first()
    )
    if not club:
        raise HTTPException(404, detail="Club not found")
    return club


@router.patch("/{club_id}", response_model=schemas.ClubOut)
def update_club(club_id: int, payload: schemas.ClubUpdate, db: Session = Depends(get_db)):
    club = get_club_or_404(club_id, db)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(club, k, v)
    db.commit()
    db.refresh(club)
    return club


@router.delete("/{club_id}", status_code=204)
def delete_club(club_id: int, db: Session = Depends(get_db)):
    club = get_club_or_404(club_id, db)
    db.delete(club)
    db.commit()


# ── Fighters currently at this club ──────────

@router.get("/{club_id}/fighters", response_model=List[schemas.FighterOut])
def club_fighters(club_id: int, db: Session = Depends(get_db)):
    get_club_or_404(club_id, db)
    histories = (
        db.query(models.FighterClubHistory)
        .filter(
            models.FighterClubHistory.club_id == club_id,
            models.FighterClubHistory.is_current == True,
        )
        .all()
    )
    return [h.fighter for h in histories]
