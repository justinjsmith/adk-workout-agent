"""Pydantic models for the swim workout domain."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# --- Enums ---


class WorkoutType(str, Enum):
    AEROBIC = "aerobic"
    THRESHOLD = "threshold"
    SPRINT = "sprint"
    DISTANCE = "distance"
    MIXED = "mixed"


class WorkoutStatus(str, Enum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    NEEDS_CORRECTION = "needs_correction"


class FlagType(str, Enum):
    UNKNOWN_ABBREVIATION = "unknown_abbreviation"
    UNKNOWN_PATTERN = "unknown_pattern"
    VALIDATION_WARNING = "validation_warning"
    CONSISTENCY_WARNING = "consistency_warning"


class RestType(str, Enum):
    REST = "rest"
    ACTIVE_REST = "active_rest"


class IntervalType(str, Enum):
    FLAT = "flat"
    RANGE = "range"
    SPLIT = "split"
    TIME_CAP = "time_cap"


# --- Component Models ---


class Rest(BaseModel):
    """Rest between repeats or sets."""

    type: RestType = RestType.REST
    seconds: Optional[int] = None
    display: Optional[str] = None  # Original notation, e.g. "R:10", "AR"


class Interval(BaseModel):
    """Interval timing for a set."""

    type: IntervalType = IntervalType.FLAT
    value: Optional[str] = None  # For flat intervals, e.g. "1:20"
    fast: Optional[str] = None  # For range intervals (L6 time)
    slow: Optional[str] = None  # For range intervals (L1 time)
    display: Optional[str] = None  # Original notation


class LaneIntervals(BaseModel):
    """Lane-specific intervals or rep counts. L6 = fastest, L1 = slowest."""

    L6: Optional[str] = None
    L5: Optional[str] = None
    L4: Optional[str] = None
    L3: Optional[str] = None
    L2: Optional[str] = None
    L1: Optional[str] = None


class Flag(BaseModel):
    """Something the agent couldn't confidently resolve."""

    type: FlagType
    text: str  # The problematic text
    context: Optional[str] = None  # Surrounding text for human review


class SetItem(BaseModel):
    """A single set within a workout section (e.g., 4x75 Kick R:10)."""

    repeats: int = 1
    distance: Optional[int] = None  # Total distance per repeat in yards
    distance_display: Optional[str] = None  # Coach's notation: "4x75", "300-400"
    stroke: Optional[str] = None  # Canonical: "Swim", "Kick", "Pull", "Choice", etc.
    stroke_short: Optional[str] = None  # Coach's abbreviation: "Sw", "K", "P", "Ch"
    equipment: list[str] = Field(default_factory=list)  # ["Fins"], ["Paddles", "Buoy"]
    interval: Optional[Interval] = None
    rest: Optional[Rest] = None
    instruction: Optional[str] = None  # "F/E, E/F, E, F", "Build", "Fast In Heats"
    lane_intervals: Optional[LaneIntervals] = None
    lane_rep_counts: Optional[LaneIntervals] = None  # When lanes do different # of reps
    raw_text: Optional[str] = None  # Original text from the email for this set


class Section(BaseModel):
    """A named section of the workout (Warm Up, Main Set, etc.)."""

    name: str  # "Warm Up", "Main Set", "Equipment Set", "Warm Down", etc.
    equipment_context: list[str] = Field(default_factory=list)  # Equipment for entire section
    sets: list[SetItem] = Field(default_factory=list)
    raw_text: Optional[str] = None


class Variant(BaseModel):
    """A named-swimmer variant workout (e.g., Friday Patricia)."""

    name: str  # "Friday Patricia"
    target_swimmers: list[str] = Field(default_factory=list)  # ["Patricia", "Will", "Dustin"]
    sections: list[Section] = Field(default_factory=list)


class YardageEstimate(BaseModel):
    """Estimated yardage totals."""

    estimated: Optional[int] = None  # Best guess for a typical lane
    by_lane: Optional[LaneIntervals] = None  # Per-lane totals when they differ


class ParseMetadata(BaseModel):
    """Metadata about the parse itself."""

    parsed_at: datetime
    agent_version: str = "0.1.0"
    model_used: str = ""
    conventions_version: Optional[str] = None
    raw_email_text: str = ""


# --- Analysis Models ---


class EffortProfileEntry(BaseModel):
    """Effort profile for a single section of the workout."""

    section: str  # Section name, e.g. "Warm Up", "Main Set"
    intensity_pct: int  # Estimated intensity 0-100
    energy_system: str  # "aerobic", "anaerobic_glycolytic", "atp_cp"


class WorkoutAnalysis(BaseModel):
    """Physiological analysis of a parsed workout."""

    energy_systems: list[str] = Field(default_factory=list)  # ["aerobic", "anaerobic_threshold"]
    workout_narrative: str = ""  # "This workout builds from..."
    coaching_intent: str = ""  # "The descending rest pattern trains..."
    type_confidence: float = 0.0  # Confidence in workout type based on physiology
    effort_profile: list[EffortProfileEntry] = Field(default_factory=list)


# --- Top-Level Workout Model ---


class Workout(BaseModel):
    """A fully parsed swim workout."""

    id: Optional[str] = None  # Auto-generated Firestore doc ID
    email_message_id: Optional[str] = None  # Gmail message ID
    email_thread_id: Optional[str] = None  # Gmail thread ID
    week_of: Optional[date] = None  # Monday of the workout week
    day_of_week: Optional[str] = None  # "monday", "tuesday", etc.
    date: Optional[date] = None  # Actual workout date
    workout_type: WorkoutType = WorkoutType.MIXED
    practice_time: Optional[str] = None  # "5:30-7:00 AM"
    location: Optional[str] = None  # "MVAC"
    variant: Optional[str] = None  # null for default workout

    status: WorkoutStatus = WorkoutStatus.PENDING_REVIEW
    confidence: float = 0.0  # 0.0 - 1.0
    flags: list[Flag] = Field(default_factory=list)

    sections: list[Section] = Field(default_factory=list)
    variants: list[Variant] = Field(default_factory=list)

    total_yardage: Optional[YardageEstimate] = None
    analysis: Optional[WorkoutAnalysis] = None
    metadata: Optional[ParseMetadata] = None

    model_config = {"populate_by_name": True}


# --- Conventions Models ---


class Abbreviation(BaseModel):
    """A known abbreviation mapping."""

    meaning: str
    category: str  # "stroke", "stroke_modifier", "equipment", "rest", "drill_modifier", etc.
    confidence: float = 1.0
    source: Optional[str] = None  # "seed", "inferred from context", "confirmed by user"


class StructuralRule(BaseModel):
    """A rule about how to interpret workout structure."""

    rule: str
    confidence: float = 1.0
    source: Optional[str] = None


class WorkoutTypeHeuristic(BaseModel):
    """A pattern that suggests a particular workout type."""

    model_config = {"populate_by_name": True}

    pattern: str
    suggests_type: WorkoutType = Field(alias="suggestsType")


class ConventionsDoc(BaseModel):
    """The conventions knowledge base the agent loads before each parse."""

    version: int = 1
    updated_at: Optional[datetime] = None
    abbreviations: dict[str, Abbreviation] = Field(default_factory=dict)
    structural_rules: list[StructuralRule] = Field(default_factory=list)
    workout_type_heuristics: list[WorkoutTypeHeuristic] = Field(default_factory=list)
