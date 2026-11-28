import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.domains.workouts.enums import WorkoutStatus

MAX_SETS_PER_EXERCISE = 10


class ORMSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class WriteSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


class LoggedSetRead(ORMSchema):
    set_number: int
    weight_kg: Decimal
    reps: int
    rir: int | None
    completed_at: datetime


class LoggedExerciseRead(ORMSchema):
    id: uuid.UUID
    position: int
    exercise_id: int
    prescribed_exercise_id: uuid.UUID | None
    target_sets: int
    target_rep_min: int | None
    target_rep_max: int | None
    target_rir: int
    suggested_weight_kg: Decimal | None
    rest_seconds: int | None = Field(description="Rest after a working set; null without a plan")
    warm_up: bool = Field(description="Ramp-up sets advised before the working sets")
    sets: list[LoggedSetRead]


class WorkoutSummary(ORMSchema):
    id: uuid.UUID
    status: WorkoutStatus
    session_name: str
    plan_session_id: uuid.UUID | None
    started_at: datetime
    finished_at: datetime | None
    session_rpe: int | None


class WorkoutDetail(WorkoutSummary):
    week_number: int | None = Field(description="Week of the plan; null when the plan is gone")
    is_deload: bool | None
    body_weight_kg: Decimal | None
    notes: str | None
    exercises: list[LoggedExerciseRead]


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------


class WorkoutStart(WriteSchema):
    plan_session_id: uuid.UUID


class SetWrite(WriteSchema):
    weight_kg: Decimal = Field(ge=0, le=999, max_digits=5, decimal_places=2)
    reps: int = Field(ge=0, le=100)
    rir: int | None = Field(default=None, ge=0, le=5)


class ExerciseReplace(WriteSchema):
    exercise_id: int


class WorkoutFinish(WriteSchema):
    session_rpe: int | None = Field(default=None, ge=1, le=10)
    notes: str | None = Field(default=None, max_length=500)
