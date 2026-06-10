from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import List, Optional
from datetime import date

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/fighters", tags=["Fighters"])


# ── helpers ──────────────────────────────────

def get_fighter_or_404(fighter_id: int, db: Session) -> models.Fighter:
    f = db.query(models.Fighter).filter(models.Fighter.id == fighter_id).first()
    if not f:
        raise HTTPException(status_code=404, detail=f"Fighter {fighter_id} not found")
    return f


def _auto_update_experience(record: models.BoxingRecord):
    """Keep experience_level in sync with total fights whenever record changes."""
    t = record.total_fights
    if record.category == "professional":
        record.experience_level = models.ExperienceLevelEnum.professional
    elif t <= 5:
        record.experience_level = models.ExperienceLevelEnum.novice
    elif t <= 15:
        record.experience_level = models.ExperienceLevelEnum.intermediate
    else:
        record.experience_level = models.ExperienceLevelEnum.advanced


# ── CRUD ─────────────────────────────────────

@router.get("/", response_model=List[schemas.FighterOut])
def list_fighters(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    county: Optional[str] = None,
    gender: Optional[models.GenderEnum] = None,
    status: Optional[models.FighterStatusEnum] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List fighters with optional filters. Supports search on name, nickname, licence."""
    q = db.query(models.Fighter)
    if county:
        q = q.filter(models.Fighter.county.ilike(f"%{county}%"))
    if gender:
        q = q.filter(models.Fighter.gender == gender)
    if status:
        q = q.filter(models.Fighter.status == status)
    if search:
        term = f"%{search}%"
        q = q.filter(or_(
            models.Fighter.first_name.ilike(term),
            models.Fighter.last_name.ilike(term),
            models.Fighter.nickname.ilike(term),
            models.Fighter.licence_number.ilike(term),
        ))
    return q.order_by(models.Fighter.last_name).offset(skip).limit(limit).all()


@router.post("/", response_model=schemas.FighterOut, status_code=201)
def create_fighter(payload: schemas.FighterCreate, db: Session = Depends(get_db)):
    """Register a new fighter. Licence number must be unique."""
    if db.query(models.Fighter).filter(
        models.Fighter.licence_number == payload.licence_number
    ).first():
        raise HTTPException(400, detail="Licence number already exists")
    if payload.id_number and db.query(models.Fighter).filter(
        models.Fighter.id_number == payload.id_number
    ).first():
        raise HTTPException(400, detail="National ID already registered")

    fighter = models.Fighter(**payload.model_dump())
    db.add(fighter)
    db.flush()  # get the id before committing

    # Always create a blank boxing record
    record = models.BoxingRecord(fighter_id=fighter.id)
    db.add(record)
    db.commit()
    db.refresh(fighter)
    return fighter


@router.get("/{fighter_id}", response_model=schemas.FighterDetail)
def get_fighter(fighter_id: int, db: Session = Depends(get_db)):
    """Full fighter profile with all related data."""
    f = (
        db.query(models.Fighter)
        .options(
            joinedload(models.Fighter.club_history).joinedload(models.FighterClubHistory.club),
            joinedload(models.Fighter.coach_assignments).joinedload(models.FighterCoach.coach),
            joinedload(models.Fighter.physical_profiles),
            joinedload(models.Fighter.medical_records),
            joinedload(models.Fighter.boxing_record),
            joinedload(models.Fighter.titles),
            joinedload(models.Fighter.suspensions),
        )
        .filter(models.Fighter.id == fighter_id)
        .first()
    )
    if not f:
        raise HTTPException(404, detail=f"Fighter {fighter_id} not found")
    return f


@router.patch("/{fighter_id}", response_model=schemas.FighterOut)
def update_fighter(
    fighter_id: int, payload: schemas.FighterUpdate, db: Session = Depends(get_db)
):
    fighter = get_fighter_or_404(fighter_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(fighter, field, value)
    db.commit()
    db.refresh(fighter)
    return fighter


@router.delete("/{fighter_id}", status_code=204)
def delete_fighter(fighter_id: int, db: Session = Depends(get_db)):
    fighter = get_fighter_or_404(fighter_id, db)
    db.delete(fighter)
    db.commit()


# ── PHYSICAL PROFILES ────────────────────────

@router.get("/{fighter_id}/physical", response_model=List[schemas.PhysicalProfileOut])
def get_physical_profiles(fighter_id: int, db: Session = Depends(get_db)):
    get_fighter_or_404(fighter_id, db)
    return (
        db.query(models.PhysicalProfile)
        .filter(models.PhysicalProfile.fighter_id == fighter_id)
        .order_by(models.PhysicalProfile.measured_on.desc())
        .all()
    )


@router.post("/{fighter_id}/physical", response_model=schemas.PhysicalProfileOut, status_code=201)
def add_physical_profile(
    fighter_id: int,
    payload: schemas.PhysicalProfileCreate,
    db: Session = Depends(get_db),
):
    get_fighter_or_404(fighter_id, db)
    profile = models.PhysicalProfile(**{**payload.model_dump(), "fighter_id": fighter_id})
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


# ── MEDICAL RECORDS ──────────────────────────

@router.get("/{fighter_id}/medical", response_model=List[schemas.MedicalRecordOut])
def get_medical_records(fighter_id: int, db: Session = Depends(get_db)):
    get_fighter_or_404(fighter_id, db)
    return (
        db.query(models.MedicalRecord)
        .filter(models.MedicalRecord.fighter_id == fighter_id)
        .order_by(models.MedicalRecord.exam_date.desc())
        .all()
    )


@router.post("/{fighter_id}/medical", response_model=schemas.MedicalRecordOut, status_code=201)
def add_medical_record(
    fighter_id: int,
    payload: schemas.MedicalRecordCreate,
    db: Session = Depends(get_db),
):
    get_fighter_or_404(fighter_id, db)
    record = models.MedicalRecord(**{**payload.model_dump(), "fighter_id": fighter_id})
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.patch("/{fighter_id}/medical/{record_id}", response_model=schemas.MedicalRecordOut)
def update_medical_record(
    fighter_id: int,
    record_id: int,
    payload: schemas.MedicalRecordUpdate,
    db: Session = Depends(get_db),
):
    get_fighter_or_404(fighter_id, db)
    rec = db.query(models.MedicalRecord).filter(
        models.MedicalRecord.id == record_id,
        models.MedicalRecord.fighter_id == fighter_id,
    ).first()
    if not rec:
        raise HTTPException(404, detail="Medical record not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rec, field, value)
    db.commit()
    db.refresh(rec)
    return rec


# ── BOXING RECORD ────────────────────────────

@router.get("/{fighter_id}/record", response_model=schemas.BoxingRecordOut)
def get_boxing_record(fighter_id: int, db: Session = Depends(get_db)):
    get_fighter_or_404(fighter_id, db)
    rec = db.query(models.BoxingRecord).filter(
        models.BoxingRecord.fighter_id == fighter_id
    ).first()
    if not rec:
        raise HTTPException(404, detail="No boxing record found — create fighter first")
    return rec


@router.patch("/{fighter_id}/record", response_model=schemas.BoxingRecordOut)
def update_boxing_record(
    fighter_id: int,
    payload: schemas.BoxingRecordUpdate,
    db: Session = Depends(get_db),
):
    """Manually adjust the boxing record (usually auto-updated via bouts endpoint)."""
    get_fighter_or_404(fighter_id, db)
    rec = db.query(models.BoxingRecord).filter(
        models.BoxingRecord.fighter_id == fighter_id
    ).first()
    if not rec:
        raise HTTPException(404, detail="Boxing record not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rec, field, value)
    _auto_update_experience(rec)
    db.commit()
    db.refresh(rec)
    return rec


# ── CLUB HISTORY ─────────────────────────────

@router.post("/{fighter_id}/clubs", response_model=schemas.FighterClubHistoryOut, status_code=201)
def assign_club(
    fighter_id: int,
    payload: schemas.FighterClubHistoryCreate,
    db: Session = Depends(get_db),
):
    """Assign or move a fighter to a club. Closes any current assignment."""
    get_fighter_or_404(fighter_id, db)
    # Mark previous club as no-longer-current
    db.query(models.FighterClubHistory).filter(
        models.FighterClubHistory.fighter_id == fighter_id,
        models.FighterClubHistory.is_current == True,
    ).update({"is_current": False, "left_date": payload.joined_date})

    entry = models.FighterClubHistory(**{**payload.model_dump(), "fighter_id": fighter_id})
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


# ── COACH ASSIGNMENTS ────────────────────────

@router.post("/{fighter_id}/coaches", response_model=schemas.FighterCoachOut, status_code=201)
def assign_coach(
    fighter_id: int,
    payload: schemas.FighterCoachCreate,
    db: Session = Depends(get_db),
):
    get_fighter_or_404(fighter_id, db)
    assignment = models.FighterCoach(**{**payload.model_dump(), "fighter_id": fighter_id})
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


# ── SUSPENSIONS ──────────────────────────────

@router.get("/{fighter_id}/suspensions", response_model=List[schemas.SuspensionOut])
def get_suspensions(fighter_id: int, db: Session = Depends(get_db)):
    get_fighter_or_404(fighter_id, db)
    return (
        db.query(models.Suspension)
        .filter(models.Suspension.fighter_id == fighter_id)
        .order_by(models.Suspension.start_date.desc())
        .all()
    )


# ── TITLES ───────────────────────────────────

@router.get("/{fighter_id}/titles", response_model=List[schemas.TitleOut])
def get_titles(fighter_id: int, db: Session = Depends(get_db)):
    get_fighter_or_404(fighter_id, db)
    return (
        db.query(models.Title)
        .filter(models.Title.fighter_id == fighter_id)
        .order_by(models.Title.won_date.desc())
        .all()
    )


# ── BOUTS ─────────────────────────────────────

@router.get("/{fighter_id}/bouts", response_model=List[schemas.BoutDetail])
def get_fighter_bouts(fighter_id: int, db: Session = Depends(get_db)):
    """All bouts for a fighter (as A or B), newest first."""
    get_fighter_or_404(fighter_id, db)
    bouts = (
        db.query(models.Bout)
        .options(
            joinedload(models.Bout.fighter_a),
            joinedload(models.Bout.fighter_b),
            joinedload(models.Bout.weight_class),
            joinedload(models.Bout.event),
        )
        .filter(
            or_(
                models.Bout.fighter_a_id == fighter_id,
                models.Bout.fighter_b_id == fighter_id,
            )
        )
        .join(models.Event)
        .order_by(models.Event.event_date.desc())
        .all()
    )
    return bouts
