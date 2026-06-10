"""
main.py — Boxing Federation of Kenya (BFK) API
FastAPI + SQLAlchemy ORM + SQLite + Static HTML frontend

Run:
    python main.py                          # direct run (recommended)
    uvicorn main:app --reload --port 8001   # dev mode with auto-reload

Open browser:
    http://127.0.0.1:8001/                  → Admin UI (HTML frontend)
    http://127.0.0.1:8001/docs              → Swagger API explorer
    http://127.0.0.1:8001/redoc             → ReDoc API docs
    http://127.0.0.1:8001/health            → Health check
"""

import os
from contextlib import asynccontextmanager
from datetime import date, timedelta
from typing import Optional

from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.database import engine, get_db, Base
from app import models

# ── Routers ───────────────────────────────────────────────────────────────────
from app.routers.fighters import router as fighters_router
from app.routers.clubs import router as clubs_router
from app.routers.coaches import router as coaches_router
from app.routers.competition import (
    weight_router,
    event_router,
    bout_router,
    title_router,
    suspension_router,
)
from app.routers.matchmaking import router as matchmaking_router


# ─────────────────────────────────────────────
# LIFESPAN
# ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create all DB tables on first start — safe to re-run, never drops data."""
    Base.metadata.create_all(bind=engine)
    yield


# ─────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────

app = FastAPI(
    title="Boxing Federation of Kenya — Admin API",
    description=(
        "Backend for the BFK matchmaking and fighter management system. "
        "Covers fighters, clubs, coaches, bouts, events, medical records, "
        "suspensions, titles, and the matchmaking suggestion engine."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─────────────────────────────────────────────
# CORS
# ─────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# API ROUTERS  — registered BEFORE static mount
# so /docs, /health, /fighters etc. are never
# swallowed by the catch-all static handler.
# ─────────────────────────────────────────────

app.include_router(fighters_router)
app.include_router(clubs_router)
app.include_router(coaches_router)
app.include_router(weight_router)
app.include_router(event_router)
app.include_router(bout_router)
app.include_router(title_router)
app.include_router(suspension_router)
app.include_router(matchmaking_router)


# ─────────────────────────────────────────────
# HEALTH & UTILITY  (also before static mount)
# ─────────────────────────────────────────────

@app.get("/health", tags=["Health"])
def health(db: Session = Depends(get_db)):
    """Database ping + service status."""
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "ok" if db_ok else "error",
        "date": str(date.today()),
    }


@app.get("/dashboard", tags=["Dashboard"])
def dashboard(db: Session = Depends(get_db)):
    """
    Single endpoint that returns all counts for the admin dashboard overview.
    The HTML frontend calls this on load to populate the stat cards.
    """
    today = date.today()
    in_30_days = today + timedelta(days=30)

    total_fighters   = db.query(models.Fighter).count()
    active_fighters  = db.query(models.Fighter).filter(models.Fighter.status == models.FighterStatusEnum.active).count()
    suspended_fighters = db.query(models.Fighter).filter(models.Fighter.status == models.FighterStatusEnum.suspended).count()
    amateur_fighters = db.query(models.BoxingRecord).filter(models.BoxingRecord.category == "amateur").count()
    pro_fighters     = db.query(models.BoxingRecord).filter(models.BoxingRecord.category == "professional").count()

    total_clubs   = db.query(models.Club).filter(models.Club.status == "active").count()
    total_coaches = db.query(models.Coach).filter(models.Coach.status == "active").count()

    total_events    = db.query(models.Event).count()
    upcoming_events = (
        db.query(models.Event)
        .filter(models.Event.status == models.EventStatusEnum.upcoming)
        .order_by(models.Event.event_date)
        .limit(5)
        .all()
    )

    total_bouts     = db.query(models.Bout).filter(models.Bout.result.isnot(None)).count()
    scheduled_bouts = db.query(models.Bout).filter(models.Bout.result.is_(None)).count()

    active_titles = db.query(models.Title).filter(models.Title.is_active == True).count()

    active_suspensions = (
        db.query(models.Suspension)
        .filter(
            models.Suspension.is_active == True,
            models.Suspension.end_date >= today,
        )
        .count()
    )

    # Medical clearances expiring within 30 days (fixed date arithmetic)
    expiring_medical = (
        db.query(models.MedicalRecord)
        .filter(
            models.MedicalRecord.cleared_to_compete == True,
            models.MedicalRecord.licence_expiry.isnot(None),
            models.MedicalRecord.licence_expiry >= today,
            models.MedicalRecord.licence_expiry <= in_30_days,
        )
        .count()
    )

    pool_available = (
        db.query(models.MatchmakingPool)
        .filter(models.MatchmakingPool.available_for_match == True)
        .count()
    )

    # Fighters per weight class (top 6, from pool entries)
    wc_dist = (
        db.query(
            models.WeightClass.name,
            models.WeightClass.gender,
            func.count(models.MatchmakingPool.id).label("count"),
        )
        .outerjoin(models.MatchmakingPool,
                   models.MatchmakingPool.weight_class_id == models.WeightClass.id)
        .group_by(models.WeightClass.id)
        .order_by(func.count(models.MatchmakingPool.id).desc())
        .limit(6)
        .all()
    )

    return {
        "fighters": {
            "total": total_fighters,
            "active": active_fighters,
            "suspended": suspended_fighters,
            "amateur": amateur_fighters,
            "professional": pro_fighters,
        },
        "clubs": total_clubs,
        "coaches": total_coaches,
        "events": {
            "total": total_events,
            "upcoming": [
                {
                    "id": e.id,
                    "name": e.name,
                    "date": str(e.event_date),
                    "venue": e.venue,
                    "county": e.county,
                    "type": e.event_type,
                    "body": e.sanctioning_body,
                }
                for e in upcoming_events
            ],
        },
        "bouts": {
            "completed": total_bouts,
            "scheduled": scheduled_bouts,
        },
        "titles":      {"active": active_titles},
        "suspensions": {"active": active_suspensions},
        "medical":     {"expiring_soon": expiring_medical},
        "matchmaking": {"pool_available": pool_available},
        "weight_class_distribution": [
            {"name": r.name, "gender": r.gender, "count": r.count}
            for r in wc_dist
        ],
    }


@app.get("/search", tags=["Search"])
def global_search(
    q: str = Query(..., min_length=2, description="Search term (min 2 chars)"),
    db: Session = Depends(get_db),
):
    """
    Cross-entity search across fighters, clubs, coaches, and events.
    Returns up to 5 hits per category — used by the UI topbar search box.
    """
    term = f"%{q}%"

    fighters = (
        db.query(models.Fighter)
        .filter(
            models.Fighter.first_name.ilike(term)
            | models.Fighter.last_name.ilike(term)
            | models.Fighter.nickname.ilike(term)
            | models.Fighter.licence_number.ilike(term)
        )
        .limit(5).all()
    )
    clubs = (
        db.query(models.Club)
        .filter(
            models.Club.name.ilike(term)
            | models.Club.bfk_affiliation_no.ilike(term)
            | models.Club.county.ilike(term)
        )
        .limit(5).all()
    )
    coaches = (
        db.query(models.Coach)
        .filter(
            models.Coach.first_name.ilike(term)
            | models.Coach.last_name.ilike(term)
            | models.Coach.licence_number.ilike(term)
        )
        .limit(5).all()
    )
    events = (
        db.query(models.Event)
        .filter(
            models.Event.name.ilike(term)
            | models.Event.venue.ilike(term)
            | models.Event.county.ilike(term)
        )
        .limit(5).all()
    )

    return {
        "query": q,
        "fighters": [{"type": "fighter", "id": f.id,
                       "label": f"{f.first_name} {f.last_name}",
                       "sub": f.licence_number, "status": f.status}
                     for f in fighters],
        "clubs":    [{"type": "club",    "id": c.id,
                       "label": c.name, "sub": c.county, "status": c.status}
                     for c in clubs],
        "coaches":  [{"type": "coach",   "id": c.id,
                       "label": f"{c.first_name} {c.last_name}",
                       "sub": c.licence_number, "status": c.status}
                     for c in coaches],
        "events":   [{"type": "event",   "id": e.id,
                       "label": e.name, "sub": str(e.event_date), "status": e.status}
                     for e in events],
        "total_results": len(fighters) + len(clubs) + len(coaches) + len(events),
    }


# ─────────────────────────────────────────────
# STATIC FRONTEND
# Must be mounted LAST — after every API route.
# FastAPI evaluates explicit routes first, so
# /docs, /health, /fighters etc. are never
# intercepted by this catch-all mount.
#
# Drop your HTML file into:  static/index.html
# ─────────────────────────────────────────────

_static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(_static_dir, exist_ok=True)   # create folder if missing

app.mount(
    "/",
    StaticFiles(directory=_static_dir, html=True),
    name="static",
)


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8001,
        reload=False,        # set True during active development
        log_level="info",
    )
