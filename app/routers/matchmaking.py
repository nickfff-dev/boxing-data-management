"""
matchmaking.py — Matchmaking pool CRUD + suggestion engine.

The suggestion engine runs every BFK/KPBC eligibility rule:
  1. Both fighters must be status=active
  2. No active suspension (end_date >= today or is_active=True)
  3. Latest medical record cleared_to_compete=True AND licence_expiry >= event_date
  4. Same weight_class_id
  5. Different clubs (current club_history)
  6. Experience level compatibility (configurable tolerance)
  7. Same gender
  8. No prior bout between the two within the last N months (configurable)
  9. Both must be available_for_match=True in the pool
  10. Walk-around weight within 3 kg of each other (optional soft check)

Each check produces a named pass/warn/fail, and a 0-100 compatibility
score is computed as a weighted sum of the passing checks.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/matchmaking", tags=["Matchmaking"])


# ─────────────────────────────────────────────────────────
# POOL  CRUD
# ─────────────────────────────────────────────────────────

@router.get("/pool", response_model=List[schemas.MatchmakingPoolOut])
def list_pool(
    weight_class_id: Optional[int] = None,
    available_only: bool = True,
    gender: Optional[models.GenderEnum] = None,
    experience_level: Optional[models.ExperienceLevelEnum] = None,
    db: Session = Depends(get_db),
):
    """
    Return all fighters currently in the matchmaking pool.
    Filter by weight class, availability, gender, experience level.
    """
    q = (
        db.query(models.MatchmakingPool)
        .options(
            joinedload(models.MatchmakingPool.fighter),
            joinedload(models.MatchmakingPool.weight_class),
        )
    )
    if available_only:
        q = q.filter(models.MatchmakingPool.available_for_match == True)
    if weight_class_id:
        q = q.filter(models.MatchmakingPool.weight_class_id == weight_class_id)

    # Filter through fighter join
    if gender or experience_level:
        q = q.join(models.Fighter, models.MatchmakingPool.fighter_id == models.Fighter.id)
        if gender:
            q = q.filter(models.Fighter.gender == gender)
        if experience_level:
            q = q.join(
                models.BoxingRecord,
                models.BoxingRecord.fighter_id == models.Fighter.id,
            ).filter(models.BoxingRecord.experience_level == experience_level)

    return q.all()


@router.post("/pool", response_model=schemas.MatchmakingPoolOut, status_code=201)
def add_to_pool(payload: schemas.MatchmakingPoolCreate, db: Session = Depends(get_db)):
    """Add a fighter to the matchmaking pool. Each fighter has at most one pool entry."""
    fighter = db.query(models.Fighter).filter(
        models.Fighter.id == payload.fighter_id
    ).first()
    if not fighter:
        raise HTTPException(404, detail="Fighter not found")

    existing = db.query(models.MatchmakingPool).filter(
        models.MatchmakingPool.fighter_id == payload.fighter_id
    ).first()
    if existing:
        raise HTTPException(
            400,
            detail="Fighter already in pool. Use PATCH /matchmaking/pool/{id} to update.",
        )

    entry = models.MatchmakingPool(**payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/pool/{entry_id}", response_model=schemas.MatchmakingPoolOut)
def get_pool_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = (
        db.query(models.MatchmakingPool)
        .options(
            joinedload(models.MatchmakingPool.fighter),
            joinedload(models.MatchmakingPool.weight_class),
        )
        .filter(models.MatchmakingPool.id == entry_id)
        .first()
    )
    if not entry:
        raise HTTPException(404, detail="Pool entry not found")
    return entry


@router.patch("/pool/{entry_id}", response_model=schemas.MatchmakingPoolOut)
def update_pool_entry(
    entry_id: int,
    payload: schemas.MatchmakingPoolUpdate,
    db: Session = Depends(get_db),
):
    entry = db.query(models.MatchmakingPool).filter(
        models.MatchmakingPool.id == entry_id
    ).first()
    if not entry:
        raise HTTPException(404, detail="Pool entry not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(entry, k, v)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/pool/{entry_id}", status_code=204)
def remove_from_pool(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(models.MatchmakingPool).filter(
        models.MatchmakingPool.id == entry_id
    ).first()
    if not entry:
        raise HTTPException(404, detail="Pool entry not found")
    db.delete(entry)
    db.commit()


@router.get("/pool/by-fighter/{fighter_id}", response_model=schemas.MatchmakingPoolOut)
def get_pool_entry_by_fighter(fighter_id: int, db: Session = Depends(get_db)):
    entry = (
        db.query(models.MatchmakingPool)
        .options(
            joinedload(models.MatchmakingPool.fighter),
            joinedload(models.MatchmakingPool.weight_class),
        )
        .filter(models.MatchmakingPool.fighter_id == fighter_id)
        .first()
    )
    if not entry:
        raise HTTPException(404, detail="Fighter not in pool")
    return entry


# ─────────────────────────────────────────────────────────
# ELIGIBILITY HELPERS
# ─────────────────────────────────────────────────────────

def _current_club_id(fighter_id: int, db: Session) -> Optional[int]:
    """Return the club_id for the fighter's current active club."""
    history = (
        db.query(models.FighterClubHistory)
        .filter(
            models.FighterClubHistory.fighter_id == fighter_id,
            models.FighterClubHistory.is_current == True,
        )
        .first()
    )
    return history.club_id if history else None


def _latest_medical(fighter_id: int, db: Session) -> Optional[models.MedicalRecord]:
    return (
        db.query(models.MedicalRecord)
        .filter(models.MedicalRecord.fighter_id == fighter_id)
        .order_by(models.MedicalRecord.exam_date.desc())
        .first()
    )


def _active_suspension(fighter_id: int, db: Session) -> Optional[models.Suspension]:
    return (
        db.query(models.Suspension)
        .filter(
            models.Suspension.fighter_id == fighter_id,
            models.Suspension.is_active == True,
            models.Suspension.end_date >= date.today(),
        )
        .first()
    )


def _prior_bout_within(
    fighter_a_id: int,
    fighter_b_id: int,
    months: int,
    db: Session,
) -> Optional[models.Bout]:
    """Check if the two fighters have faced each other within `months` months."""
    cutoff = date.today() - timedelta(days=months * 30)
    return (
        db.query(models.Bout)
        .join(models.Event, models.Bout.event_id == models.Event.id)
        .filter(
            or_(
                and_(
                    models.Bout.fighter_a_id == fighter_a_id,
                    models.Bout.fighter_b_id == fighter_b_id,
                ),
                and_(
                    models.Bout.fighter_a_id == fighter_b_id,
                    models.Bout.fighter_b_id == fighter_a_id,
                ),
            ),
            models.Event.event_date >= cutoff,
        )
        .first()
    )


def _experience_gap(lvl_a: str, lvl_b: str) -> int:
    """Return numeric gap between experience levels (0 = same, 3 = max)."""
    order = {
        models.ExperienceLevelEnum.novice: 0,
        models.ExperienceLevelEnum.intermediate: 1,
        models.ExperienceLevelEnum.advanced: 2,
        models.ExperienceLevelEnum.professional: 3,
    }
    return abs(order.get(lvl_a, 0) - order.get(lvl_b, 0))


# ─────────────────────────────────────────────────────────
# SUGGESTION ENGINE
# ─────────────────────────────────────────────────────────

_WEIGHTS = {
    "active_status":        15,
    "no_suspension":        15,
    "medical_clear":        15,
    "same_weight_class":    15,
    "different_clubs":      10,
    "experience_match":     10,
    "same_gender":          10,
    "no_recent_bout":        5,
    "walk_around_close":     5,
}
_MAX_SCORE = sum(_WEIGHTS.values())   # 100


def _run_eligibility(
    pool_a: models.MatchmakingPool,
    pool_b: models.MatchmakingPool,
    check_date: date,
    max_experience_gap: int,
    no_repeat_months: int,
    db: Session,
) -> dict:
    """
    Run all eligibility checks for a candidate pair.
    Returns a dict with check results, score, and warnings.
    """
    fa = pool_a.fighter
    fb = pool_b.fighter
    checks = {}
    warnings = []
    score = 0.0

    # 1. Active status
    a_active = fa.status == models.FighterStatusEnum.active
    b_active = fb.status == models.FighterStatusEnum.active
    checks["active_status"] = {
        "pass": a_active and b_active,
        "detail": f"{fa.first_name}: {'✓' if a_active else '✗'}  {fb.first_name}: {'✓' if b_active else '✗'}",
    }
    if checks["active_status"]["pass"]:
        score += _WEIGHTS["active_status"]
    else:
        warnings.append("One or both fighters are not in active status")

    # 2. No active suspension
    susp_a = _active_suspension(fa.id, db)
    susp_b = _active_suspension(fb.id, db)
    checks["no_suspension"] = {
        "pass": susp_a is None and susp_b is None,
        "detail": f"{fa.first_name}: {'✓' if not susp_a else '✗ suspended until ' + str(susp_a.end_date)}  "
                  f"{fb.first_name}: {'✓' if not susp_b else '✗ suspended until ' + str(susp_b.end_date)}",
    }
    if checks["no_suspension"]["pass"]:
        score += _WEIGHTS["no_suspension"]
    else:
        warnings.append("One or both fighters have an active suspension")

    # 3. Medical clearance + licence valid
    med_a = _latest_medical(fa.id, db)
    med_b = _latest_medical(fb.id, db)

    def med_ok(med: Optional[models.MedicalRecord]) -> bool:
        if not med or not med.cleared_to_compete:
            return False
        if med.licence_expiry and med.licence_expiry < check_date:
            return False
        return True

    a_med_ok = med_ok(med_a)
    b_med_ok = med_ok(med_b)
    checks["medical_clear"] = {
        "pass": a_med_ok and b_med_ok,
        "detail": f"{fa.first_name}: {'✓' if a_med_ok else '✗'}  {fb.first_name}: {'✓' if b_med_ok else '✗'}",
    }
    if checks["medical_clear"]["pass"]:
        score += _WEIGHTS["medical_clear"]
    else:
        warnings.append("One or both fighters lack valid medical clearance")

    # 4. Same weight class
    same_wc = pool_a.weight_class_id == pool_b.weight_class_id
    checks["same_weight_class"] = {
        "pass": same_wc,
        "detail": f"A: class_id={pool_a.weight_class_id}  B: class_id={pool_b.weight_class_id}",
    }
    if same_wc:
        score += _WEIGHTS["same_weight_class"]
    else:
        warnings.append("Fighters are in different weight classes")

    # 5. Different clubs
    club_a = _current_club_id(fa.id, db)
    club_b = _current_club_id(fb.id, db)
    diff_clubs = club_a != club_b or (club_a is None and club_b is None)
    checks["different_clubs"] = {
        "pass": diff_clubs,
        "detail": f"A club_id={club_a}  B club_id={club_b}",
    }
    if diff_clubs:
        score += _WEIGHTS["different_clubs"]
    else:
        warnings.append("Both fighters are from the same club — not permitted under BFK rules")

    # 6. Experience level gap
    rec_a = fa.boxing_record
    rec_b = fb.boxing_record
    lvl_a = rec_a.experience_level if rec_a else models.ExperienceLevelEnum.novice
    lvl_b = rec_b.experience_level if rec_b else models.ExperienceLevelEnum.novice
    gap = _experience_gap(lvl_a, lvl_b)
    exp_ok = gap <= max_experience_gap
    checks["experience_match"] = {
        "pass": exp_ok,
        "detail": f"{fa.first_name}: {lvl_a}  {fb.first_name}: {lvl_b}  gap={gap}",
    }
    if exp_ok:
        score += _WEIGHTS["experience_match"]
    else:
        warnings.append(f"Experience gap ({gap}) exceeds allowed maximum ({max_experience_gap})")

    # 7. Same gender (hard BFK rule)
    same_gender = fa.gender == fb.gender
    checks["same_gender"] = {
        "pass": same_gender,
        "detail": f"{fa.first_name}: {fa.gender}  {fb.first_name}: {fb.gender}",
    }
    if same_gender:
        score += _WEIGHTS["same_gender"]
    else:
        warnings.append("Fighters are different genders")

    # 8. No recent bout between them
    prior = _prior_bout_within(fa.id, fb.id, no_repeat_months, db)
    no_recent = prior is None
    checks["no_recent_bout"] = {
        "pass": no_recent,
        "detail": f"No bout in last {no_repeat_months} months: {'✓' if no_recent else '✗ (bout #' + str(prior.id) + ')'}",
    }
    if no_recent:
        score += _WEIGHTS["no_recent_bout"]
    else:
        warnings.append(f"These fighters met within the last {no_repeat_months} months")

    # 9. Walk-around weight difference (soft check ≤3 kg)
    wa_a = pool_a.walk_around_weight_kg
    wa_b = pool_b.walk_around_weight_kg
    if wa_a and wa_b:
        wa_diff = abs(wa_a - wa_b)
        wa_ok = wa_diff <= 3.0
        checks["walk_around_close"] = {
            "pass": wa_ok,
            "detail": f"A: {wa_a} kg  B: {wa_b} kg  diff={wa_diff:.1f} kg",
        }
        if wa_ok:
            score += _WEIGHTS["walk_around_close"]
        elif wa_diff > 3.0:
            warnings.append(f"Walk-around weight difference ({wa_diff:.1f} kg) is large")
    else:
        checks["walk_around_close"] = {
            "pass": True,
            "detail": "Walk-around weight not recorded — skipped",
        }
        score += _WEIGHTS["walk_around_close"]  # neutral — don't penalise missing data

    pct = round(score / _MAX_SCORE * 100, 1)
    return {"checks": checks, "score": pct, "warnings": warnings}


# ─────────────────────────────────────────────────────────
# SUGGEST ENDPOINT
# ─────────────────────────────────────────────────────────

@router.get("/suggest", response_model=List[schemas.MatchSuggestion])
def suggest_matches(
    weight_class_id: Optional[int] = Query(None, description="Restrict to one weight class"),
    gender: Optional[models.GenderEnum] = Query(None),
    experience_level: Optional[models.ExperienceLevelEnum] = Query(None),
    max_experience_gap: int = Query(1, ge=0, le=3, description="0=exact match, 1=one tier, 2=two"),
    no_repeat_months: int = Query(6, ge=0, description="Block pairs who fought within N months"),
    min_score: float = Query(50.0, ge=0, le=100, description="Minimum compatibility score to include"),
    event_date: Optional[date] = Query(None, description="Use this date for licence expiry checks"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Generate ranked match suggestions from available pool fighters.

    The engine:
    1. Loads all available pool entries (filtered by params).
    2. Generates every distinct pair within the same weight class and gender.
    3. Runs full BFK/KPBC eligibility checks on each pair.
    4. Returns pairs sorted by compatibility score descending.

    Only pairs where ALL hard-fail checks pass are included unless
    their score still meets min_score (useful to show borderline pairs with warnings).
    """
    check_date = event_date or date.today()

    # Load candidate pool entries with all needed relationships
    q = (
        db.query(models.MatchmakingPool)
        .options(
            joinedload(models.MatchmakingPool.fighter)
            .joinedload(models.Fighter.boxing_record),
            joinedload(models.MatchmakingPool.weight_class),
        )
        .filter(models.MatchmakingPool.available_for_match == True)
    )
    if weight_class_id:
        q = q.filter(models.MatchmakingPool.weight_class_id == weight_class_id)
    if gender:
        q = q.join(models.Fighter, models.MatchmakingPool.fighter_id == models.Fighter.id)
        q = q.filter(models.Fighter.gender == gender)
    if experience_level:
        q = (
            q.join(models.Fighter, models.MatchmakingPool.fighter_id == models.Fighter.id,
                   isouter=True)
            .join(models.BoxingRecord,
                  models.BoxingRecord.fighter_id == models.Fighter.id, isouter=True)
            .filter(models.BoxingRecord.experience_level == experience_level)
        )

    pool_entries = q.all()

    if len(pool_entries) < 2:
        return []

    suggestions: List[schemas.MatchSuggestion] = []

    # Generate unique pairs
    for i in range(len(pool_entries)):
        for j in range(i + 1, len(pool_entries)):
            pool_a = pool_entries[i]
            pool_b = pool_entries[j]

            # Hard gate: must be same weight class (engine also checks, but skip early)
            if pool_a.weight_class_id != pool_b.weight_class_id:
                continue

            result = _run_eligibility(
                pool_a, pool_b, check_date, max_experience_gap, no_repeat_months, db
            )

            if result["score"] < min_score:
                continue

            suggestions.append(
                schemas.MatchSuggestion(
                    fighter_a=schemas.FighterOut.model_validate(pool_a.fighter),
                    fighter_b=schemas.FighterOut.model_validate(pool_b.fighter),
                    weight_class=schemas.WeightClassOut.model_validate(pool_a.weight_class),
                    compatibility_score=result["score"],
                    checks=result["checks"],
                    warnings=result["warnings"],
                )
            )

    # Sort by score descending
    suggestions.sort(key=lambda s: s.compatibility_score, reverse=True)
    return suggestions[:limit]


# ─────────────────────────────────────────────────────────
# ELIGIBILITY CHECK FOR A SPECIFIC PAIR
# ─────────────────────────────────────────────────────────

@router.get("/check", response_model=schemas.MatchSuggestion)
def check_pair_eligibility(
    fighter_a_id: int = Query(...),
    fighter_b_id: int = Query(...),
    weight_class_id: int = Query(...),
    event_date: Optional[date] = Query(None),
    max_experience_gap: int = Query(1, ge=0, le=3),
    no_repeat_months: int = Query(6, ge=0),
    db: Session = Depends(get_db),
):
    """
    Run all eligibility checks for a specific pair of fighters
    at a given weight class, without them needing to be in the pool.
    Useful for quick ad-hoc checks before creating a bout.
    """
    check_date = event_date or date.today()

    fa = db.query(models.Fighter).options(
        joinedload(models.Fighter.boxing_record)
    ).filter(models.Fighter.id == fighter_a_id).first()
    fb = db.query(models.Fighter).options(
        joinedload(models.Fighter.boxing_record)
    ).filter(models.Fighter.id == fighter_b_id).first()

    if not fa:
        raise HTTPException(404, detail=f"Fighter A (id={fighter_a_id}) not found")
    if not fb:
        raise HTTPException(404, detail=f"Fighter B (id={fighter_b_id}) not found")
    if fighter_a_id == fighter_b_id:
        raise HTTPException(400, detail="Fighter A and Fighter B must be different")

    wc = db.query(models.WeightClass).filter(
        models.WeightClass.id == weight_class_id
    ).first()
    if not wc:
        raise HTTPException(404, detail="Weight class not found")

    # Build synthetic pool entries so we can reuse the engine
    pool_a = models.MatchmakingPool(
        fighter_id=fa.id,
        fighter=fa,
        weight_class_id=weight_class_id,
        weight_class=wc,
    )
    pool_b = models.MatchmakingPool(
        fighter_id=fb.id,
        fighter=fb,
        weight_class_id=weight_class_id,
        weight_class=wc,
    )

    result = _run_eligibility(
        pool_a, pool_b, check_date, max_experience_gap, no_repeat_months, db
    )

    return schemas.MatchSuggestion(
        fighter_a=schemas.FighterOut.model_validate(fa),
        fighter_b=schemas.FighterOut.model_validate(fb),
        weight_class=schemas.WeightClassOut.model_validate(wc),
        compatibility_score=result["score"],
        checks=result["checks"],
        warnings=result["warnings"],
    )


# ─────────────────────────────────────────────────────────
# DASHBOARD STATS
# ─────────────────────────────────────────────────────────

@router.get("/stats", tags=["Matchmaking"])
def pool_stats(db: Session = Depends(get_db)):
    """Quick summary stats used by the matchmaking dashboard."""
    total = db.query(models.MatchmakingPool).count()
    available = db.query(models.MatchmakingPool).filter(
        models.MatchmakingPool.available_for_match == True
    ).count()

    # Break down by weight class
    from sqlalchemy import func
    wc_counts = (
        db.query(
            models.WeightClass.name,
            models.WeightClass.gender,
            func.count(models.MatchmakingPool.id).label("count"),
        )
        .join(models.MatchmakingPool,
              models.MatchmakingPool.weight_class_id == models.WeightClass.id)
        .filter(models.MatchmakingPool.available_for_match == True)
        .group_by(models.WeightClass.id)
        .all()
    )

    return {
        "total_in_pool": total,
        "available_for_match": available,
        "by_weight_class": [
            {"weight_class": r.name, "gender": r.gender, "count": r.count}
            for r in wc_counts
        ],
    }
