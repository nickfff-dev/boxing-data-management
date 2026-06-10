"""
Pydantic v2 schemas (request bodies + response shapes) for every entity.

Convention:
  - <Entity>Base     — shared fields
  - <Entity>Create   — used in POST bodies (no id/timestamps)
  - <Entity>Update   — used in PATCH bodies (all fields Optional)
  - <Entity>Out      — returned by API (includes id, timestamps, computed)
  - <Entity>Detail   — extended response with nested relationships
"""

from __future__ import annotations
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models import (
    FighterStatusEnum, GenderEnum, StanceEnum, ExperienceLevelEnum,
    ClubTypeEnum, WeightClassCategoryEnum, GoverningBodyEnum,
    EventTypeEnum, EventStatusEnum, BoutTypeEnum, BoutResultEnum,
    WinMethodEnum, SuspensionTypeEnum, PreferredBoutTypeEnum,
)


# ─────────────────────────────────────────────
# CLUB
# ─────────────────────────────────────────────

class ClubBase(BaseModel):
    name: str = Field(..., max_length=150)
    county: str = Field(..., max_length=80)
    town: Optional[str] = None
    head_coach: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None
    bfk_affiliation_no: str = Field(..., max_length=30)
    type: ClubTypeEnum = ClubTypeEnum.amateur
    insurance_expiry: Optional[date] = None
    last_audit_date: Optional[date] = None
    facilities: Optional[str] = None
    status: str = "active"


class ClubCreate(ClubBase):
    pass


class ClubUpdate(BaseModel):
    name: Optional[str] = None
    county: Optional[str] = None
    town: Optional[str] = None
    head_coach: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None
    type: Optional[ClubTypeEnum] = None
    insurance_expiry: Optional[date] = None
    last_audit_date: Optional[date] = None
    facilities: Optional[str] = None
    status: Optional[str] = None


class ClubOut(ClubBase):
    id: int
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class ClubDetail(ClubOut):
    coaches: List["CoachOut"] = []
    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# COACH
# ─────────────────────────────────────────────

class CoachBase(BaseModel):
    first_name: str = Field(..., max_length=80)
    last_name: str = Field(..., max_length=80)
    licence_number: str = Field(..., max_length=30)
    phone: Optional[str] = None
    email: Optional[str] = None
    county: Optional[str] = None
    date_of_birth: Optional[date] = None
    club_id: Optional[int] = None
    certifications: Optional[str] = None
    years_coaching: int = 0
    status: str = "active"
    notes: Optional[str] = None


class CoachCreate(CoachBase):
    pass


class CoachUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    county: Optional[str] = None
    club_id: Optional[int] = None
    certifications: Optional[str] = None
    years_coaching: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class CoachOut(CoachBase):
    id: int
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# WEIGHT CLASS
# ─────────────────────────────────────────────

class WeightClassBase(BaseModel):
    name: str = Field(..., max_length=80)
    min_kg: Optional[float] = None
    max_kg: float
    gender: GenderEnum
    category: WeightClassCategoryEnum
    governing_body: GoverningBodyEnum = GoverningBodyEnum.bfk
    is_active: bool = True


class WeightClassCreate(WeightClassBase):
    pass


class WeightClassUpdate(BaseModel):
    name: Optional[str] = None
    min_kg: Optional[float] = None
    max_kg: Optional[float] = None
    is_active: Optional[bool] = None


class WeightClassOut(WeightClassBase):
    id: int
    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# FIGHTER CLUB HISTORY
# ─────────────────────────────────────────────

class FighterClubHistoryBase(BaseModel):
    fighter_id: int
    club_id: int
    joined_date: date
    left_date: Optional[date] = None
    is_current: bool = True
    notes: Optional[str] = None


class FighterClubHistoryCreate(FighterClubHistoryBase):
    pass


class FighterClubHistoryOut(FighterClubHistoryBase):
    id: int
    club: Optional[ClubOut] = None
    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# FIGHTER COACH ASSIGNMENT
# ─────────────────────────────────────────────

class FighterCoachBase(BaseModel):
    fighter_id: int
    coach_id: int
    is_primary: bool = True
    role: str = "Head Trainer"
    assigned_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: bool = True


class FighterCoachCreate(FighterCoachBase):
    pass


class FighterCoachOut(FighterCoachBase):
    id: int
    coach: Optional[CoachOut] = None
    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# PHYSICAL PROFILE
# ─────────────────────────────────────────────

class PhysicalProfileBase(BaseModel):
    fighter_id: int
    weight_kg: float = Field(..., gt=30, lt=200)
    height_cm: Optional[float] = None
    reach_cm: Optional[float] = None
    stance: StanceEnum = StanceEnum.orthodox
    measured_on: date
    measured_by: Optional[str] = None
    notes: Optional[str] = None


class PhysicalProfileCreate(PhysicalProfileBase):
    pass


class PhysicalProfileUpdate(BaseModel):
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    reach_cm: Optional[float] = None
    stance: Optional[StanceEnum] = None
    notes: Optional[str] = None


class PhysicalProfileOut(PhysicalProfileBase):
    id: int
    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# MEDICAL RECORD
# ─────────────────────────────────────────────

class MedicalRecordBase(BaseModel):
    fighter_id: int
    exam_date: date
    doctor_name: str = Field(..., max_length=120)
    doctor_facility: Optional[str] = None
    cleared_to_compete: bool = False
    blood_pressure: Optional[str] = None
    ecg_result: Optional[str] = None
    eye_test_result: Optional[str] = None
    hiv_status: Optional[str] = None
    hepatitis_status: Optional[str] = None
    neurological_exam: Optional[str] = None
    weight_at_exam_kg: Optional[float] = None
    licence_expiry: Optional[date] = None
    notes: Optional[str] = None


class MedicalRecordCreate(MedicalRecordBase):
    pass


class MedicalRecordUpdate(BaseModel):
    cleared_to_compete: Optional[bool] = None
    blood_pressure: Optional[str] = None
    ecg_result: Optional[str] = None
    eye_test_result: Optional[str] = None
    hiv_status: Optional[str] = None
    hepatitis_status: Optional[str] = None
    neurological_exam: Optional[str] = None
    licence_expiry: Optional[date] = None
    notes: Optional[str] = None


class MedicalRecordOut(MedicalRecordBase):
    id: int
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# BOXING RECORD
# ─────────────────────────────────────────────

class BoxingRecordBase(BaseModel):
    fighter_id: int
    total_fights: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    wins_by_ko: int = 0
    wins_by_tko: int = 0
    wins_by_decision: int = 0
    losses_by_ko: int = 0
    losses_by_tko: int = 0
    losses_by_decision: int = 0
    no_contests: int = 0
    experience_level: ExperienceLevelEnum = ExperienceLevelEnum.novice
    category: str = "amateur"


class BoxingRecordCreate(BoxingRecordBase):
    pass


class BoxingRecordUpdate(BaseModel):
    total_fights: Optional[int] = None
    wins: Optional[int] = None
    losses: Optional[int] = None
    draws: Optional[int] = None
    wins_by_ko: Optional[int] = None
    wins_by_tko: Optional[int] = None
    wins_by_decision: Optional[int] = None
    losses_by_ko: Optional[int] = None
    losses_by_tko: Optional[int] = None
    losses_by_decision: Optional[int] = None
    no_contests: Optional[int] = None
    experience_level: Optional[ExperienceLevelEnum] = None
    category: Optional[str] = None


class BoxingRecordOut(BoxingRecordBase):
    id: int
    updated_at: Optional[datetime] = None

    @property
    def ko_rate(self) -> Optional[float]:
        return round((self.wins_by_ko + self.wins_by_tko) / self.wins * 100, 1) if self.wins else 0.0

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# FIGHTER  (main entity — kept last so nested schemas resolve)
# ─────────────────────────────────────────────

class FighterBase(BaseModel):
    first_name: str = Field(..., max_length=80)
    last_name: str = Field(..., max_length=80)
    nickname: Optional[str] = None
    date_of_birth: date
    gender: GenderEnum
    nationality: str = "Kenyan"
    county: Optional[str] = None
    town: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    id_number: Optional[str] = None
    passport_number: Optional[str] = None
    blood_type: Optional[str] = None
    status: FighterStatusEnum = FighterStatusEnum.active


class FighterCreate(FighterBase):
    licence_number: str = Field(..., max_length=30)


class FighterUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    nickname: Optional[str] = None
    county: Optional[str] = None
    town: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    passport_number: Optional[str] = None
    blood_type: Optional[str] = None
    status: Optional[FighterStatusEnum] = None


class FighterOut(FighterBase):
    id: int
    licence_number: str
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class FighterDetail(FighterOut):
    """Full profile — used on /fighters/{id} endpoint."""
    club_history: List[FighterClubHistoryOut] = []
    coach_assignments: List[FighterCoachOut] = []
    physical_profiles: List[PhysicalProfileOut] = []
    medical_records: List[MedicalRecordOut] = []
    boxing_record: Optional[BoxingRecordOut] = None
    titles: List["TitleOut"] = []
    suspensions: List["SuspensionOut"] = []
    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# EVENT
# ─────────────────────────────────────────────

class EventBase(BaseModel):
    name: str = Field(..., max_length=200)
    event_date: date
    venue: Optional[str] = None
    county: Optional[str] = None
    event_type: EventTypeEnum = EventTypeEnum.amateur
    sanctioning_body: GoverningBodyEnum = GoverningBodyEnum.bfk
    promoter: Optional[str] = None
    promoter_phone: Optional[str] = None
    head_official: Optional[str] = None
    status: EventStatusEnum = EventStatusEnum.upcoming
    notes: Optional[str] = None


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    name: Optional[str] = None
    event_date: Optional[date] = None
    venue: Optional[str] = None
    county: Optional[str] = None
    event_type: Optional[EventTypeEnum] = None
    sanctioning_body: Optional[GoverningBodyEnum] = None
    promoter: Optional[str] = None
    head_official: Optional[str] = None
    status: Optional[EventStatusEnum] = None
    notes: Optional[str] = None


class EventOut(EventBase):
    id: int
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class EventDetail(EventOut):
    bouts: List["BoutOut"] = []
    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# BOUT
# ─────────────────────────────────────────────

class BoutBase(BaseModel):
    event_id: int
    weight_class_id: int
    fighter_a_id: int
    fighter_b_id: int
    scheduled_rounds: int = Field(3, ge=1, le=12)
    bout_type: BoutTypeEnum = BoutTypeEnum.non_title
    title_at_stake: Optional[str] = None


class BoutCreate(BoutBase):
    bout_number: Optional[str] = None


class BoutResultUpdate(BaseModel):
    """Separate schema — you record a bout first, then update the result."""
    actual_rounds_fought: Optional[int] = None
    result: Optional[BoutResultEnum] = None
    winner_id: Optional[int] = None
    win_method: Optional[WinMethodEnum] = None
    win_round: Optional[int] = None
    win_time: Optional[str] = None
    judge1_name: Optional[str] = None
    judge1_score_a: Optional[int] = None
    judge1_score_b: Optional[int] = None
    judge2_name: Optional[str] = None
    judge2_score_a: Optional[int] = None
    judge2_score_b: Optional[int] = None
    judge3_name: Optional[str] = None
    judge3_score_a: Optional[int] = None
    judge3_score_b: Optional[int] = None
    referee: Optional[str] = None
    notes: Optional[str] = None


class BoutOut(BoutBase):
    id: int
    bout_number: Optional[str] = None
    actual_rounds_fought: Optional[int] = None
    result: Optional[BoutResultEnum] = None
    winner_id: Optional[int] = None
    win_method: Optional[WinMethodEnum] = None
    win_round: Optional[int] = None
    win_time: Optional[str] = None
    judge1_name: Optional[str] = None
    judge1_score_a: Optional[int] = None
    judge1_score_b: Optional[int] = None
    judge2_name: Optional[str] = None
    judge2_score_a: Optional[int] = None
    judge2_score_b: Optional[int] = None
    judge3_name: Optional[str] = None
    judge3_score_a: Optional[int] = None
    judge3_score_b: Optional[int] = None
    referee: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class BoutDetail(BoutOut):
    fighter_a: Optional[FighterOut] = None
    fighter_b: Optional[FighterOut] = None
    winner: Optional[FighterOut] = None
    weight_class: Optional[WeightClassOut] = None
    event: Optional[EventOut] = None
    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# TITLE
# ─────────────────────────────────────────────

class TitleBase(BaseModel):
    fighter_id: int
    title_name: str = Field(..., max_length=150)
    governing_body: Optional[str] = None
    weight_class: Optional[str] = None
    won_date: Optional[date] = None
    won_at_event_id: Optional[int] = None
    opponent_defeated: Optional[str] = None
    win_method: Optional[str] = None
    lost_date: Optional[date] = None
    vacated_date: Optional[date] = None
    vacated_reason: Optional[str] = None
    is_active: bool = True
    successful_defences: int = 0
    notes: Optional[str] = None


class TitleCreate(TitleBase):
    pass


class TitleUpdate(BaseModel):
    title_name: Optional[str] = None
    lost_date: Optional[date] = None
    vacated_date: Optional[date] = None
    vacated_reason: Optional[str] = None
    is_active: Optional[bool] = None
    successful_defences: Optional[int] = None
    notes: Optional[str] = None


class TitleOut(TitleBase):
    id: int
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# SUSPENSION
# ─────────────────────────────────────────────

class SuspensionBase(BaseModel):
    fighter_id: int
    suspension_type: SuspensionTypeEnum
    reason: str
    rule_reference: Optional[str] = None
    start_date: date
    end_date: date
    imposed_by: Optional[str] = None
    approved_by: Optional[str] = None
    conditions: Optional[str] = None
    related_bout_id: Optional[int] = None
    fine_amount_kes: Optional[float] = None
    is_active: bool = True
    notes: Optional[str] = None


class SuspensionCreate(SuspensionBase):
    pass


class SuspensionUpdate(BaseModel):
    end_date: Optional[date] = None
    conditions: Optional[str] = None
    is_active: Optional[bool] = None
    lifted_date: Optional[date] = None
    lifted_by: Optional[str] = None
    notes: Optional[str] = None


class SuspensionOut(SuspensionBase):
    id: int
    lifted_date: Optional[date] = None
    lifted_by: Optional[str] = None
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# MATCHMAKING POOL
# ─────────────────────────────────────────────

class MatchmakingPoolBase(BaseModel):
    fighter_id: int
    weight_class_id: int
    available_for_match: bool = True
    preferred_bout_type: PreferredBoutTypeEnum = PreferredBoutTypeEnum.non_title
    preferred_opponent_level: Optional[str] = None
    walk_around_weight_kg: Optional[float] = None
    available_from: Optional[date] = None
    available_until: Optional[date] = None
    target_event_id: Optional[int] = None
    notes: Optional[str] = None


class MatchmakingPoolCreate(MatchmakingPoolBase):
    pass


class MatchmakingPoolUpdate(BaseModel):
    available_for_match: Optional[bool] = None
    preferred_bout_type: Optional[PreferredBoutTypeEnum] = None
    preferred_opponent_level: Optional[str] = None
    walk_around_weight_kg: Optional[float] = None
    available_from: Optional[date] = None
    available_until: Optional[date] = None
    target_event_id: Optional[int] = None
    notes: Optional[str] = None


class MatchmakingPoolOut(MatchmakingPoolBase):
    id: int
    added_at: Optional[datetime] = None
    fighter: Optional[FighterOut] = None
    weight_class: Optional[WeightClassOut] = None
    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# MATCHMAKING SUGGESTION  (not stored — computed on the fly)
# ─────────────────────────────────────────────

class MatchSuggestion(BaseModel):
    fighter_a: FighterOut
    fighter_b: FighterOut
    weight_class: WeightClassOut
    compatibility_score: float = Field(..., description="0–100 match quality score")
    checks: dict = Field(..., description="Dict of eligibility check results")
    warnings: List[str] = []


# ─────────────────────────────────────────────
# PAGINATION WRAPPER
# ─────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    results: list


# Forward references
FighterDetail.model_rebuild()
EventDetail.model_rebuild()
ClubDetail.model_rebuild()
