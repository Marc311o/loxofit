import uuid
from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domains.plans.enums import PlanStatus

MAX_SESSIONS_PER_WEEK = 7
MAX_EXERCISES_PER_SESSION = 15


class ORMSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class WriteSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


class PrescribedExerciseRead(ORMSchema):
    id: uuid.UUID
    exercise_id: int
    slot: int
    sets: int
    rep_min: int | None
    rep_max: int | None


class PlanSessionRead(ORMSchema):
    id: uuid.UUID
    position: int
    name: str
    max_minutes: int
    weekday: int | None
    exercises: list[PrescribedExerciseRead]


class PlanWeekRead(ORMSchema):
    id: uuid.UUID
    week_number: int
    rir: int
    is_deload: bool
    sessions: list[PlanSessionRead]


class MuscleTargetRead(ORMSchema):
    muscle_id: int
    priority: float


class PlanSummary(ORMSchema):
    id: uuid.UUID
    name: str
    status: PlanStatus
    num_weeks: int
    config_id: int
    created_at: datetime
    updated_at: datetime


class PlanDetail(PlanSummary):
    weeks: list[PlanWeekRead]
    muscle_targets: list[MuscleTargetRead]


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------


class PlanCreate(WriteSchema):
    name: str = Field(min_length=1, max_length=100)
    num_weeks: int = Field(default=5, ge=2, le=12)


class PlanUpdate(WriteSchema):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    num_weeks: int | None = Field(default=None, ge=2, le=12)


class PrescribedExerciseWrite(WriteSchema):
    id: uuid.UUID | None = None
    exercise_id: int = Field(ge=1)
    sets: int = Field(ge=1, le=10)
    rep_min: int | None = Field(default=None, ge=1, le=50)
    rep_max: int | None = Field(default=None, ge=1, le=50)

    @model_validator(mode="after")
    def _check_rep_range(self) -> Self:
        if self.rep_min is not None and self.rep_max is not None and self.rep_min > self.rep_max:
            raise ValueError("rep_min must not exceed rep_max")
        return self


class PlanSessionWrite(WriteSchema):
    id: uuid.UUID | None = None
    name: str = Field(min_length=1, max_length=50)
    max_minutes: int = Field(default=60, ge=20, le=180)
    weekday: int | None = Field(default=None, ge=1, le=7)
    exercises: list[PrescribedExerciseWrite] = Field(
        default_factory=list, max_length=MAX_EXERCISES_PER_SESSION
    )

    @model_validator(mode="after")
    def _check_unique_exercises(self) -> Self:
        ids = [e.exercise_id for e in self.exercises]
        if len(ids) != len(set(ids)):
            raise ValueError("an exercise can appear only once in a session")
        return self


class BaseWeekWrite(WriteSchema):
    sessions: list[PlanSessionWrite] = Field(max_length=MAX_SESSIONS_PER_WEEK)

    @model_validator(mode="after")
    def _check_weekdays(self) -> Self:
        days = [s.weekday for s in self.sessions if s.weekday is not None]
        if len(days) != len(set(days)):
            raise ValueError("two sessions cannot share a weekday")
        return self


class MuscleTargetWrite(WriteSchema):
    muscle_id: int = Field(ge=1)
    priority: float = Field(ge=0, le=3)


class MuscleTargetsWrite(WriteSchema):
    targets: list[MuscleTargetWrite]

    @model_validator(mode="after")
    def _check_unique_muscles(self) -> Self:
        ids = [t.muscle_id for t in self.targets]
        if len(ids) != len(set(ids)):
            raise ValueError("a muscle can appear only once")
        return self
