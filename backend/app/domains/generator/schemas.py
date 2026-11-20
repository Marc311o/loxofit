import uuid
from collections import Counter
from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domains.generator.enums import GenerationStatus, SplitTemplate
from app.domains.plans.schemas import MAX_SESSIONS_PER_WEEK, MuscleTargetWrite
from app.engine.focus import Focus, Template, template_focuses

SEED_MAX = 2**31 - 1

FOCUS_NAMES = {
    Focus.FULL_BODY: "Full body",
    Focus.UPPER: "Upper",
    Focus.LOWER: "Lower",
    Focus.PUSH: "Push",
    Focus.PULL: "Pull",
}


class WriteSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------


class SessionRequest(WriteSchema):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    weekday: int | None = Field(default=None, ge=1, le=7)
    max_minutes: int = Field(default=60, ge=20, le=180)
    focus: Focus | None = None  # custom template only - otherwise the template decides


class GenerationRequest(WriteSchema):
    """What the user fixes; the generator chooses the exercises and their sets.
    Equipment always comes from the user's profile."""

    template: SplitTemplate
    sessions: list[SessionRequest] = Field(min_length=1, max_length=MAX_SESSIONS_PER_WEEK)
    num_weeks: int = Field(default=5, ge=2, le=12)
    targets: list[MuscleTargetWrite] = Field(default_factory=list)
    seed: int | None = Field(default=None, ge=0, le=SEED_MAX)  # None - a new random plan

    @model_validator(mode="after")
    def _check(self) -> Self:
        custom = self.template == SplitTemplate.CUSTOM
        if custom and any(s.focus is None for s in self.sessions):
            raise ValueError("a custom split needs the focus of every session")
        if not custom and any(s.focus is not None for s in self.sessions):
            raise ValueError("the template sets the focus - leave it out or use 'custom'")
        days = [s.weekday for s in self.sessions if s.weekday is not None]
        if len(days) != len(set(days)):
            raise ValueError("two sessions cannot share a weekday")
        muscles = [t.muscle_id for t in self.targets]
        if len(muscles) != len(set(muscles)):
            raise ValueError("a muscle can appear only once")
        return self

    def focuses(self) -> tuple[Focus, ...]:
        if self.template == SplitTemplate.CUSTOM:
            return tuple(s.focus for s in self.sessions if s.focus is not None)
        return template_focuses(Template(self.template.value), len(self.sessions))

    def session_names(self) -> list[str]:
        """The given names; the others from the focus - "Upper A", "Upper B" when it repeats."""
        focuses = self.focuses()
        repeated = {f for f, n in Counter(focuses).items() if n > 1}
        seen: Counter[Focus] = Counter()
        names = []
        for session, focus in zip(self.sessions, focuses, strict=True):
            seen[focus] += 1
            letter = f" {chr(ord('A') + seen[focus] - 1)}" if focus in repeated else ""
            names.append(session.name or FOCUS_NAMES[focus] + letter)
        return names


class SaveGeneratedPlan(WriteSchema):
    name: str = Field(min_length=1, max_length=100)


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


class GenerationProgress(BaseModel):
    evaluations: int
    budget: int
    best_score: float | None


class GeneratedExercise(BaseModel):
    exercise_id: int
    sets: int


class GeneratedSession(BaseModel):
    name: str
    weekday: int | None
    max_minutes: int
    focus: Focus
    exercises: list[GeneratedExercise]


class GenerationRunRead(BaseModel):
    id: uuid.UUID
    status: GenerationStatus
    request: GenerationRequest
    seed: int
    algorithm: str
    budget: int
    config_id: int
    progress: GenerationProgress | None  # while running
    evaluations: int | None
    score: float | None
    max_score: float | None
    sessions: list[GeneratedSession] | None  # when done
    history: list[tuple[int, float]] | None  # (evaluations, best score) at every improvement
    error: str | None
    plan_id: uuid.UUID | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
