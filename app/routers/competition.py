"""
competition.py — routers for weight_classes, events, bouts, titles, suspensions.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import List, Optional
from datetime import date

from app.database import get_db
from app import models, schemas

# ─────────────────────────────────────────────
# WEIGHT CLASSES
# ─────────────────────────────────────────────

weight_router = APIRouter(prefix="/weight-classes", tags=["Weight Classes"])


@weight_router.get("/", response_model=List[schemas.WeightClassOut])
def list_weight_classes(
    gender: Optional[models.GenderEnum] = None,
    category: Optional[models.WeightClassCategoryEnum] = None,
    governing_body: Optional[models.GoverningBodyEnum] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.WeightClass).filter(models.WeightClass.is_active == True)
    if gender:
        q = q.filter(models.WeightClass.gender == gender)
    if category:
        q = q.filter(models.WeightClass.category == category)
    if governing_body:
        q = q.filter(models.WeightClass.governing_body == governing_body)
    return q.order_by(models.WeightClass.max_kg).all()


@weight_router.post("/", response_model=schemas.WeightClassOut, status_code=201)
def create_weight_class(payload: schemas.WeightClassCreate, db: Session = Depends(get_db)):
    wc = models.WeightClass(**payload.model_dump())
    db.add(wc)
    db.commit()
    db.refresh(wc)
    return wc


@weight_router.get("/{wc_id}", response_model=schemas.WeightClassOut)
def get_weight_class(wc_id: int, db: Session = Depends(get_db)):
    wc = db.query(models.WeightClass).filter(models.WeightClass.id == wc_id).first()
    if not wc:
        raise HTTPException(404, detail="Weight class not found")
    return wc


@weight_router.patch("/{wc_id}", response_model=schemas.WeightClassOut)
def update_weight_class(
    wc_id: int, payload: schemas.WeightClassUpdate, db: Session = Depends(get_db)
):
    wc = db.query(models.WeightClass).filter(models.WeightClass.id == wc_id).first()
    if not wc:
        raise HTTPException(404, detail="Weight class not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(wc, k, v)
    db.commit()
    db.refresh(wc)
    return wc


# ─────────────────────────────────────────────
# EVENTS
# ─────────────────────────────────────────────

event_router = APIRouter(prefix="/events", tags=["Events"])


@event_router.get("/", response_model=List[schemas.EventOut])
def list_events(
    skip: int = 0,
    limit: int = 50,
    status: Optional[models.EventStatusEnum] = None,
    event_type: Optional[models.EventTypeEnum] = None,
    county: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Event)
    if status:
        q = q.filter(models.Event.status == status)
    if event_type:
        q = q.filter(models.Event.event_type == event_type)
    if county:
        q = q.filter(models.Event.county.ilike(f"%{county}%"))
    if from_date:
        q = q.filter(models.Event.event_date >= from_date)
    if to_date:
        q = q.filter(models.Event.event_date <= to_date)
    return q.order_by(models.Event.event_date.desc()).offset(skip).limit(limit).all()


@event_router.post("/", response_model=schemas.EventOut, status_code=201)
def create_event(payload: schemas.EventCreate, db: Session = Depends(get_db)):
    event = models.Event(**payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@event_router.get("/{event_id}", response_model=schemas.EventDetail)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = (
        db.query(models.Event)
        .options(
            joinedload(models.Event.bouts)
            .joinedload(models.Bout.fighter_a),
            joinedload(models.Event.bouts)
            .joinedload(models.Bout.fighter_b),
        )
        .filter(models.Event.id == event_id)
        .first()
    )
    if not event:
        raise HTTPException(404, detail="Event not found")
    return event


@event_router.patch("/{event_id}", response_model=schemas.EventOut)
def update_event(
    event_id: int, payload: schemas.EventUpdate, db: Session = Depends(get_db)
):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(404, detail="Event not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(event, k, v)
    db.commit()
    db.refresh(event)
    return event


@event_router.delete("/{event_id}", status_code=204)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(404, detail="Event not found")
    db.delete(event)
    db.commit()


# ─────────────────────────────────────────────
# BOUTS
# ─────────────────────────────────────────────

bout_router = APIRouter(prefix="/bouts", tags=["Bouts"])


def _auto_number(db: Session) -> str:
    """Auto-generate bout number as #XXXX."""
    last = db.query(models.Bout).order_by(models.Bout.id.desc()).first()
    next_num = (last.id + 1) if last else 1001
    return f"#{next_num}"


def _update_records_after_bout(bout: models.Bout, db: Session):
    """
    After a result is saved, increment the boxing_record counters
    for both fighters. Idempotent — only called when result is set.
    """
    if not bout.result or not bout.win_method:
        return

    def get_rec(fighter_id):
        r = db.query(models.BoxingRecord).filter(
            models.BoxingRecord.fighter_id == fighter_id
        ).first()
        if not r:
            r = models.BoxingRecord(fighter_id=fighter_id)
            db.add(r)
        return r

    rec_a = get_rec(bout.fighter_a_id)
    rec_b = get_rec(bout.fighter_b_id)

    # total fights
    rec_a.total_fights += 1
    rec_b.total_fights += 1

    method = bout.win_method.value if hasattr(bout.win_method, "value") else bout.win_method

    if bout.result == models.BoutResultEnum.fighter_a:
        rec_a.wins += 1
        rec_b.losses += 1
        if method == "KO":
            rec_a.wins_by_ko += 1
            rec_b.losses_by_ko += 1
        elif method in ("TKO", "TKO_medical", "TKO_corner"):
            rec_a.wins_by_tko += 1
            rec_b.losses_by_tko += 1
        elif method in ("UD", "MD", "SD"):
            rec_a.wins_by_decision += 1
            rec_b.losses_by_decision += 1

    elif bout.result == models.BoutResultEnum.fighter_b:
        rec_b.wins += 1
        rec_a.losses += 1
        if method == "KO":
            rec_b.wins_by_ko += 1
            rec_a.losses_by_ko += 1
        elif method in ("TKO", "TKO_medical", "TKO_corner"):
            rec_b.wins_by_tko += 1
            rec_a.losses_by_tko += 1
        elif method in ("UD", "MD", "SD"):
            rec_b.wins_by_decision += 1
            rec_a.losses_by_decision += 1

    elif bout.result in (
        models.BoutResultEnum.draw, models.BoutResultEnum.technical_draw
    ):
        rec_a.draws += 1
        rec_b.draws += 1

    elif bout.result == models.BoutResultEnum.no_contest:
        rec_a.no_contests += 1
        rec_b.no_contests += 1

    # Sync experience level
    from app.routers.fighters import _auto_update_experience
    _auto_update_experience(rec_a)
    _auto_update_experience(rec_b)


@bout_router.get("/", response_model=List[schemas.BoutOut])
def list_bouts(
    skip: int = 0,
    limit: int = 50,
    event_id: Optional[int] = None,
    fighter_id: Optional[int] = None,
    weight_class_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Bout)
    if event_id:
        q = q.filter(models.Bout.event_id == event_id)
    if fighter_id:
        q = q.filter(
            or_(
                models.Bout.fighter_a_id == fighter_id,
                models.Bout.fighter_b_id == fighter_id,
            )
        )
    if weight_class_id:
        q = q.filter(models.Bout.weight_class_id == weight_class_id)
    return q.order_by(models.Bout.id.desc()).offset(skip).limit(limit).all()


@bout_router.post("/", response_model=schemas.BoutOut, status_code=201)
def create_bout(payload: schemas.BoutCreate, db: Session = Depends(get_db)):
    """Schedule a bout (no result yet)."""
    if payload.fighter_a_id == payload.fighter_b_id:
        raise HTTPException(400, detail="Fighter A and Fighter B must be different")

    # Verify both fighters exist
    for fid in [payload.fighter_a_id, payload.fighter_b_id]:
        if not db.query(models.Fighter).filter(models.Fighter.id == fid).first():
            raise HTTPException(404, detail=f"Fighter {fid} not found")

    data = payload.model_dump()
    if not data.get("bout_number"):
        data["bout_number"] = _auto_number(db)

    bout = models.Bout(**data)
    db.add(bout)
    db.commit()
    db.refresh(bout)
    return bout


@bout_router.get("/{bout_id}", response_model=schemas.BoutDetail)
def get_bout(bout_id: int, db: Session = Depends(get_db)):
    bout = (
        db.query(models.Bout)
        .options(
            joinedload(models.Bout.fighter_a),
            joinedload(models.Bout.fighter_b),
            joinedload(models.Bout.winner),
            joinedload(models.Bout.weight_class),
            joinedload(models.Bout.event),
        )
        .filter(models.Bout.id == bout_id)
        .first()
    )
    if not bout:
        raise HTTPException(404, detail="Bout not found")
    return bout


@bout_router.patch("/{bout_id}/result", response_model=schemas.BoutOut)
def record_bout_result(
    bout_id: int,
    payload: schemas.BoutResultUpdate,
    db: Session = Depends(get_db),
):
    """
    Record or update the result of a bout.
    Also auto-updates both fighters' boxing_record rows.
    """
    bout = db.query(models.Bout).filter(models.Bout.id == bout_id).first()
    if not bout:
        raise HTTPException(404, detail="Bout not found")

    already_had_result = bout.result is not None

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(bout, k, v)

    # Only update records if result is freshly set (not re-patching non-result fields)
    if not already_had_result and bout.result is not None:
        _update_records_after_bout(bout, db)

    db.commit()
    db.refresh(bout)
    return bout


@bout_router.delete("/{bout_id}", status_code=204)
def delete_bout(bout_id: int, db: Session = Depends(get_db)):
    bout = db.query(models.Bout).filter(models.Bout.id == bout_id).first()
    if not bout:
        raise HTTPException(404, detail="Bout not found")
    db.delete(bout)
    db.commit()


# ─────────────────────────────────────────────
# TITLES
# ─────────────────────────────────────────────

title_router = APIRouter(prefix="/titles", tags=["Titles"])


@title_router.get("/", response_model=List[schemas.TitleOut])
def list_titles(
    is_active: Optional[bool] = None,
    governing_body: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Title)
    if is_active is not None:
        q = q.filter(models.Title.is_active == is_active)
    if governing_body:
        q = q.filter(models.Title.governing_body.ilike(f"%{governing_body}%"))
    return q.order_by(models.Title.won_date.desc()).all()


@title_router.post("/", response_model=schemas.TitleOut, status_code=201)
def create_title(payload: schemas.TitleCreate, db: Session = Depends(get_db)):
    title = models.Title(**payload.model_dump())
    db.add(title)
    db.commit()
    db.refresh(title)
    return title


@title_router.get("/{title_id}", response_model=schemas.TitleOut)
def get_title(title_id: int, db: Session = Depends(get_db)):
    t = db.query(models.Title).filter(models.Title.id == title_id).first()
    if not t:
        raise HTTPException(404, detail="Title not found")
    return t


@title_router.patch("/{title_id}", response_model=schemas.TitleOut)
def update_title(
    title_id: int, payload: schemas.TitleUpdate, db: Session = Depends(get_db)
):
    t = db.query(models.Title).filter(models.Title.id == title_id).first()
    if not t:
        raise HTTPException(404, detail="Title not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(t, k, v)
    db.commit()
    db.refresh(t)
    return t


# ─────────────────────────────────────────────
# SUSPENSIONS
# ─────────────────────────────────────────────

suspension_router = APIRouter(prefix="/suspensions", tags=["Suspensions"])


@suspension_router.get("/", response_model=List[schemas.SuspensionOut])
def list_suspensions(
    is_active: Optional[bool] = None,
    suspension_type: Optional[models.SuspensionTypeEnum] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Suspension)
    if is_active is not None:
        q = q.filter(models.Suspension.is_active == is_active)
    if suspension_type:
        q = q.filter(models.Suspension.suspension_type == suspension_type)
    return q.order_by(models.Suspension.start_date.desc()).all()


@suspension_router.post("/", response_model=schemas.SuspensionOut, status_code=201)
def create_suspension(payload: schemas.SuspensionCreate, db: Session = Depends(get_db)):
    # Check the fighter exists
    if not db.query(models.Fighter).filter(
        models.Fighter.id == payload.fighter_id
    ).first():
        raise HTTPException(404, detail="Fighter not found")

    suspension = models.Suspension(**payload.model_dump())
    db.add(suspension)

    # Also flip fighter status to suspended
    fighter = db.query(models.Fighter).filter(
        models.Fighter.id == payload.fighter_id
    ).first()
    fighter.status = models.FighterStatusEnum.suspended

    db.commit()
    db.refresh(suspension)
    return suspension


@suspension_router.get("/{suspension_id}", response_model=schemas.SuspensionOut)
def get_suspension(suspension_id: int, db: Session = Depends(get_db)):
    s = db.query(models.Suspension).filter(models.Suspension.id == suspension_id).first()
    if not s:
        raise HTTPException(404, detail="Suspension not found")
    return s


@suspension_router.patch("/{suspension_id}", response_model=schemas.SuspensionOut)
def update_suspension(
    suspension_id: int,
    payload: schemas.SuspensionUpdate,
    db: Session = Depends(get_db),
):
    s = db.query(models.Suspension).filter(models.Suspension.id == suspension_id).first()
    if not s:
        raise HTTPException(404, detail="Suspension not found")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(s, k, v)

    # If lifting the suspension, restore fighter to active
    if payload.is_active is False or payload.lifted_date is not None:
        s.is_active = False
        fighter = db.query(models.Fighter).filter(
            models.Fighter.id == s.fighter_id
        ).first()
        if fighter:
            # Only mark active if no other active suspension remains
            other_active = db.query(models.Suspension).filter(
                models.Suspension.fighter_id == s.fighter_id,
                models.Suspension.is_active == True,
                models.Suspension.id != s.id,
            ).count()
            if other_active == 0:
                fighter.status = models.FighterStatusEnum.active

    db.commit()
    db.refresh(s)
    return s
