"""
SQLAlchemy ORM models for the Boxing Federation of Kenya (BFK) database.
Mirrors the MySQL schema discussed in the design session, adapted for SQLite.
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Date, DateTime,
    Text, Enum, ForeignKey, CheckConstraint, UniqueConstraint, event
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


# ─────────────────────────────────────────────
# ENUM TYPES
# ─────────────────────────────────────────────

class FighterStatusEnum(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    retired = "retired"
    suspended = "suspended"
    deceased = "deceased"


class GenderEnum(str, enum.Enum):
    male = "male"
    female = "female"


class StanceEnum(str, enum.Enum):
    orthodox = "orthodox"
    southpaw = "southpaw"
    switch = "switch"


class ExperienceLevelEnum(str, enum.Enum):
    novice = "novice"           # 0-5 bouts
    intermediate = "intermediate"  # 6-15 bouts
    advanced = "advanced"       # 16+ bouts amateur
    professional = "professional"


class ClubTypeEnum(str, enum.Enum):
    amateur = "amateur"
    professional = "professional"
    mixed = "mixed"


class WeightClassCategoryEnum(str, enum.Enum):
    amateur_male = "amateur_male"
    amateur_female = "amateur_female"
    professional = "professional"


class GoverningBodyEnum(str, enum.Enum):
    bfk = "BFK"
    kpbc = "KPBC"
    iba = "IBA"
    abu = "ABU"
    wbc = "WBC"
    wbo = "WBO"
    ibf = "IBF"
    wba = "WBA"


class EventTypeEnum(str, enum.Enum):
    amateur = "amateur"
    professional = "professional"
    mixed = "mixed"


class EventStatusEnum(str, enum.Enum):
    draft = "draft"
    upcoming = "upcoming"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class BoutTypeEnum(str, enum.Enum):
    title = "title"
    title_defence = "title_defence"
    elimination = "elimination"
    non_title = "non_title"
    exhibition = "exhibition"


class BoutResultEnum(str, enum.Enum):
    fighter_a = "fighter_a"
    fighter_b = "fighter_b"
    draw = "draw"
    no_contest = "no_contest"
    technical_draw = "technical_draw"


class WinMethodEnum(str, enum.Enum):
    ko = "KO"
    tko = "TKO"
    tko_medical = "TKO_medical"
    tko_corner = "TKO_corner"
    ud = "UD"        # unanimous decision
    md = "MD"        # majority decision
    sd = "SD"        # split decision
    dq = "DQ"        # disqualification
    rtd = "RTD"      # retired/corner stopped
    nc = "NC"        # no contest


class SuspensionTypeEnum(str, enum.Enum):
    medical = "medical"
    disciplinary = "disciplinary"
    administrative = "administrative"
    doping = "doping"


class PreferredBoutTypeEnum(str, enum.Enum):
    title = "title"
    title_defence = "title_defence"
    non_title = "non_title"
    any = "any"


# ─────────────────────────────────────────────
# CLUBS
# ─────────────────────────────────────────────

class Club(Base):
    __tablename__ = "clubs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    county = Column(String(80), nullable=False)
    town = Column(String(80))
    head_coach = Column(String(120))
    contact_phone = Column(String(20))
    contact_email = Column(String(120))
    address = Column(String(250))
    bfk_affiliation_no = Column(String(30), unique=True, nullable=False)
    type = Column(Enum(ClubTypeEnum), nullable=False, default=ClubTypeEnum.amateur)
    insurance_expiry = Column(Date)
    last_audit_date = Column(Date)
    facilities = Column(Text)
    status = Column(String(20), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    coaches = relationship("Coach", back_populates="club")
    fighter_history = relationship("FighterClubHistory", back_populates="club")


# ─────────────────────────────────────────────
# COACHES
# ─────────────────────────────────────────────

class Coach(Base):
    __tablename__ = "coaches"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(80), nullable=False)
    last_name = Column(String(80), nullable=False)
    licence_number = Column(String(30), unique=True, nullable=False, index=True)
    phone = Column(String(20))
    email = Column(String(120))
    county = Column(String(80))
    date_of_birth = Column(Date)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=True)
    certifications = Column(Text)   # comma-separated e.g. "IBA L3,KPBC,First Aid"
    years_coaching = Column(Integer, default=0)
    status = Column(String(20), default="active")
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    club = relationship("Club", back_populates="coaches")
    fighter_assignments = relationship("FighterCoach", back_populates="coach")


# ─────────────────────────────────────────────
# WEIGHT CLASSES
# ─────────────────────────────────────────────

class WeightClass(Base):
    __tablename__ = "weight_classes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(80), nullable=False)              # e.g. "Lightweight"
    min_kg = Column(Float, nullable=True)                  # None = no lower bound
    max_kg = Column(Float, nullable=False)
    gender = Column(Enum(GenderEnum), nullable=False)
    category = Column(Enum(WeightClassCategoryEnum), nullable=False)
    governing_body = Column(Enum(GoverningBodyEnum), nullable=False, default=GoverningBodyEnum.bfk)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint("name", "gender", "category", "governing_body", name="uq_weight_class"),
    )

    # Relationships
    bouts = relationship("Bout", back_populates="weight_class")
    pool_entries = relationship("MatchmakingPool", back_populates="weight_class")


# ─────────────────────────────────────────────
# FIGHTERS  (core identity table)
# ─────────────────────────────────────────────

class Fighter(Base):
    __tablename__ = "fighters"

    id = Column(Integer, primary_key=True, index=True)
    licence_number = Column(String(30), unique=True, nullable=False, index=True)
    first_name = Column(String(80), nullable=False)
    last_name = Column(String(80), nullable=False)
    nickname = Column(String(80))
    date_of_birth = Column(Date, nullable=False)
    gender = Column(Enum(GenderEnum), nullable=False)
    nationality = Column(String(60), default="Kenyan")
    county = Column(String(80))
    town = Column(String(80))
    phone = Column(String(20))
    email = Column(String(120))
    id_number = Column(String(20), unique=True)         # National ID
    passport_number = Column(String(20))
    blood_type = Column(String(5))                      # A+, B-, O+, etc.
    status = Column(Enum(FighterStatusEnum), nullable=False, default=FighterStatusEnum.active)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    club_history = relationship("FighterClubHistory", back_populates="fighter",
                                order_by="FighterClubHistory.joined_date.desc()")
    coach_assignments = relationship("FighterCoach", back_populates="fighter")
    physical_profiles = relationship("PhysicalProfile", back_populates="fighter",
                                     order_by="PhysicalProfile.measured_on.desc()")
    medical_records = relationship("MedicalRecord", back_populates="fighter",
                                   order_by="MedicalRecord.exam_date.desc()")
    boxing_record = relationship("BoxingRecord", back_populates="fighter", uselist=False)
    titles = relationship("Title", back_populates="fighter",
                          foreign_keys="Title.fighter_id")
    suspensions = relationship("Suspension", back_populates="fighter")
    pool_entry = relationship("MatchmakingPool", back_populates="fighter", uselist=False)

    # Bouts where this fighter appears as fighter_a or fighter_b
    bouts_as_a = relationship("Bout", foreign_keys="Bout.fighter_a_id", back_populates="fighter_a")
    bouts_as_b = relationship("Bout", foreign_keys="Bout.fighter_b_id", back_populates="fighter_b")


# ─────────────────────────────────────────────
# FIGHTER ↔ CLUB  (history, not just current)
# ─────────────────────────────────────────────

class FighterClubHistory(Base):
    __tablename__ = "fighter_club_history"

    id = Column(Integer, primary_key=True, index=True)
    fighter_id = Column(Integer, ForeignKey("fighters.id"), nullable=False, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False, index=True)
    joined_date = Column(Date, nullable=False)
    left_date = Column(Date, nullable=True)   # NULL = still at this club
    is_current = Column(Boolean, default=True)
    notes = Column(String(250))

    fighter = relationship("Fighter", back_populates="club_history")
    club = relationship("Club", back_populates="fighter_history")


# ─────────────────────────────────────────────
# FIGHTER ↔ COACH  (primary + corner coaches)
# ─────────────────────────────────────────────

class FighterCoach(Base):
    __tablename__ = "fighter_coach"

    id = Column(Integer, primary_key=True, index=True)
    fighter_id = Column(Integer, ForeignKey("fighters.id"), nullable=False, index=True)
    coach_id = Column(Integer, ForeignKey("coaches.id"), nullable=False, index=True)
    is_primary = Column(Boolean, default=True)
    role = Column(String(60), default="Head Trainer")  # Head Trainer, Corner, S&C
    assigned_date = Column(Date)
    end_date = Column(Date)
    is_active = Column(Boolean, default=True)

    fighter = relationship("Fighter", back_populates="coach_assignments")
    coach = relationship("Coach", back_populates="fighter_assignments")


# ─────────────────────────────────────────────
# PHYSICAL PROFILES  (time-series measurements)
# ─────────────────────────────────────────────

class PhysicalProfile(Base):
    __tablename__ = "physical_profiles"

    id = Column(Integer, primary_key=True, index=True)
    fighter_id = Column(Integer, ForeignKey("fighters.id"), nullable=False, index=True)
    weight_kg = Column(Float, nullable=False)
    height_cm = Column(Float)
    reach_cm = Column(Float)
    stance = Column(Enum(StanceEnum), default=StanceEnum.orthodox)
    measured_on = Column(Date, nullable=False)
    measured_by = Column(String(80))    # Official or club name
    notes = Column(String(250))

    fighter = relationship("Fighter", back_populates="physical_profiles")


# ─────────────────────────────────────────────
# MEDICAL RECORDS
# ─────────────────────────────────────────────

class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id = Column(Integer, primary_key=True, index=True)
    fighter_id = Column(Integer, ForeignKey("fighters.id"), nullable=False, index=True)
    exam_date = Column(Date, nullable=False)
    doctor_name = Column(String(120), nullable=False)
    doctor_facility = Column(String(150))
    cleared_to_compete = Column(Boolean, nullable=False, default=False)
    blood_pressure = Column(String(15))     # e.g. "120/80"
    ecg_result = Column(String(30))         # Normal / Abnormal / Pending
    eye_test_result = Column(String(20))    # e.g. "20/20"
    hiv_status = Column(String(20))         # Negative / Positive
    hepatitis_status = Column(String(20))   # Negative / Positive
    neurological_exam = Column(String(30))  # Normal / Abnormal
    weight_at_exam_kg = Column(Float)
    licence_expiry = Column(Date)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    fighter = relationship("Fighter", back_populates="medical_records")


# ─────────────────────────────────────────────
# BOXING RECORD  (denormalised running totals)
# ─────────────────────────────────────────────

class BoxingRecord(Base):
    """
    Denormalised summary kept in sync whenever a Bout result is saved.
    Avoids recounting across the full bouts table on every matchmaking query.
    """
    __tablename__ = "boxing_records"

    id = Column(Integer, primary_key=True, index=True)
    fighter_id = Column(Integer, ForeignKey("fighters.id"), nullable=False, unique=True, index=True)
    total_fights = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    draws = Column(Integer, default=0)
    wins_by_ko = Column(Integer, default=0)
    wins_by_tko = Column(Integer, default=0)
    wins_by_decision = Column(Integer, default=0)
    losses_by_ko = Column(Integer, default=0)
    losses_by_tko = Column(Integer, default=0)
    losses_by_decision = Column(Integer, default=0)
    no_contests = Column(Integer, default=0)
    experience_level = Column(Enum(ExperienceLevelEnum), default=ExperienceLevelEnum.novice)
    category = Column(String(20), default="amateur")    # "amateur" or "professional"
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    fighter = relationship("Fighter", back_populates="boxing_record")


# ─────────────────────────────────────────────
# EVENTS
# ─────────────────────────────────────────────

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    event_date = Column(Date, nullable=False, index=True)
    venue = Column(String(150))
    county = Column(String(80))
    event_type = Column(Enum(EventTypeEnum), nullable=False, default=EventTypeEnum.amateur)
    sanctioning_body = Column(Enum(GoverningBodyEnum), nullable=False, default=GoverningBodyEnum.bfk)
    promoter = Column(String(120))
    promoter_phone = Column(String(20))
    head_official = Column(String(120))
    status = Column(Enum(EventStatusEnum), default=EventStatusEnum.upcoming)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    bouts = relationship("Bout", back_populates="event", order_by="Bout.id")


# ─────────────────────────────────────────────
# BOUTS
# ─────────────────────────────────────────────

class Bout(Base):
    __tablename__ = "bouts"

    id = Column(Integer, primary_key=True, index=True)
    bout_number = Column(String(12), unique=True)   # e.g. "#2406"
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    weight_class_id = Column(Integer, ForeignKey("weight_classes.id"), nullable=False)
    fighter_a_id = Column(Integer, ForeignKey("fighters.id"), nullable=False)
    fighter_b_id = Column(Integer, ForeignKey("fighters.id"), nullable=False)

    # Pre-fight
    scheduled_rounds = Column(Integer, nullable=False, default=3)
    bout_type = Column(Enum(BoutTypeEnum), default=BoutTypeEnum.non_title)
    title_at_stake = Column(String(150))            # e.g. "Kenya National Lightweight Title"

    # Result
    actual_rounds_fought = Column(Integer)
    result = Column(Enum(BoutResultEnum))
    winner_id = Column(Integer, ForeignKey("fighters.id"), nullable=True)
    win_method = Column(Enum(WinMethodEnum))
    win_round = Column(Integer)
    win_time = Column(String(8))                    # e.g. "2:31"

    # Scorecards (judges 1-3, scores for A and B)
    judge1_name = Column(String(80))
    judge1_score_a = Column(Integer)
    judge1_score_b = Column(Integer)
    judge2_name = Column(String(80))
    judge2_score_a = Column(Integer)
    judge2_score_b = Column(Integer)
    judge3_name = Column(String(80))
    judge3_score_a = Column(Integer)
    judge3_score_b = Column(Integer)

    referee = Column(String(80))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    event = relationship("Event", back_populates="bouts")
    weight_class = relationship("WeightClass", back_populates="bouts")
    fighter_a = relationship("Fighter", foreign_keys=[fighter_a_id], back_populates="bouts_as_a")
    fighter_b = relationship("Fighter", foreign_keys=[fighter_b_id], back_populates="bouts_as_b")
    winner = relationship("Fighter", foreign_keys=[winner_id])

    __table_args__ = (
        CheckConstraint("fighter_a_id != fighter_b_id", name="ck_different_fighters"),
    )


# ─────────────────────────────────────────────
# TITLES  (championship belts)
# ─────────────────────────────────────────────

class Title(Base):
    __tablename__ = "titles"

    id = Column(Integer, primary_key=True, index=True)
    fighter_id = Column(Integer, ForeignKey("fighters.id"), nullable=False, index=True)
    title_name = Column(String(150), nullable=False)
    governing_body = Column(String(60))
    weight_class = Column(String(80))
    won_date = Column(Date)
    won_at_event_id = Column(Integer, ForeignKey("events.id"), nullable=True)
    opponent_defeated = Column(String(120))
    win_method = Column(String(30))
    lost_date = Column(Date)
    vacated_date = Column(Date)
    vacated_reason = Column(Text)
    is_active = Column(Boolean, default=True)
    successful_defences = Column(Integer, default=0)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    fighter = relationship("Fighter", foreign_keys=[fighter_id], back_populates="titles")
    won_at_event = relationship("Event", foreign_keys=[won_at_event_id])


# ─────────────────────────────────────────────
# SUSPENSIONS
# ─────────────────────────────────────────────

class Suspension(Base):
    __tablename__ = "suspensions"

    id = Column(Integer, primary_key=True, index=True)
    fighter_id = Column(Integer, ForeignKey("fighters.id"), nullable=False, index=True)
    suspension_type = Column(Enum(SuspensionTypeEnum), nullable=False)
    reason = Column(Text, nullable=False)
    rule_reference = Column(String(100))            # e.g. "BFK Rule 4.8"
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    imposed_by = Column(String(150))
    approved_by = Column(String(150))
    conditions = Column(Text)                       # what must happen before reinstatement
    related_bout_id = Column(Integer, ForeignKey("bouts.id"), nullable=True)
    fine_amount_kes = Column(Float)                 # any monetary fine in KES
    is_active = Column(Boolean, default=True)
    lifted_date = Column(Date)
    lifted_by = Column(String(150))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    fighter = relationship("Fighter", back_populates="suspensions")
    related_bout = relationship("Bout", foreign_keys=[related_bout_id])


# ─────────────────────────────────────────────
# MATCHMAKING POOL
# ─────────────────────────────────────────────

class MatchmakingPool(Base):
    __tablename__ = "matchmaking_pool"

    id = Column(Integer, primary_key=True, index=True)
    fighter_id = Column(Integer, ForeignKey("fighters.id"), nullable=False, unique=True, index=True)
    weight_class_id = Column(Integer, ForeignKey("weight_classes.id"), nullable=False)
    available_for_match = Column(Boolean, default=True)
    preferred_bout_type = Column(Enum(PreferredBoutTypeEnum), default=PreferredBoutTypeEnum.non_title)
    preferred_opponent_level = Column(String(60))   # e.g. "Advanced, Professional"
    walk_around_weight_kg = Column(Float)            # real weight between camps
    available_from = Column(Date)
    available_until = Column(Date)                   # optional deadline
    target_event_id = Column(Integer, ForeignKey("events.id"), nullable=True)
    notes = Column(Text)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    fighter = relationship("Fighter", back_populates="pool_entry")
    weight_class = relationship("WeightClass", back_populates="pool_entries")
    target_event = relationship("Event", foreign_keys=[target_event_id])
