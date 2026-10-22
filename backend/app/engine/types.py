from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum


class Role(StrEnum):
    """Role of a muscle in an exercise."""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    STABILIZER = "stabilizer"


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ExerciseSpec:
    """What the engine needs to know about a catalog exercise."""

    code: str
    is_compound: bool
    muscle_roles: Mapping[str, Role] = field(hash=False, compare=False)
    tempo: str | None = None
    is_unilateral: bool = False

    def primary_muscles(self) -> frozenset[str]:
        return frozenset(m for m, r in self.muscle_roles.items() if r == Role.PRIMARY)


@dataclass(frozen=True, slots=True)
class MuscleTarget:
    """Weekly volume landmarks of one muscle, in effective sets."""

    mev: float  # minimum effective volume
    mav_upper: float  # upper bound of maximum adaptive volume
    mrv: float  # maximum recoverable volume
    priority: float = 1.0  # weight in the objective; 0 = ignore the muscle

    def __post_init__(self) -> None:
        if not 0 <= self.mev < self.mav_upper <= self.mrv:
            raise ValueError(
                f"Expected 0 <= mev < mav_upper <= mrv, got {self.mev}, {self.mav_upper}, {self.mrv}"
            )
        if self.priority < 0:
            raise ValueError(f"priority must be >= 0, got {self.priority}")


MuscleTargets = Mapping[str, MuscleTarget]  # muscle code -> landmarks


@dataclass(frozen=True, slots=True)
class EngineConfig:
    """Model parameters - a snapshot of a ModelConfig row plus engine constants."""

    role_weights: Mapping[Role, float] = field(hash=False)

    # Benefit function and penalties
    curve_k: float = 3.0
    penalty_lambda: float = 0.05
    time_penalty: float = 0.1  # per minute over the session limit

    # Timing (seconds)
    rest_compound_s: int = 150
    rest_isolation_s: int = 90
    transitions_s: int = 90
    warmup_s: int = 300  # general warm-up time
    explosive_phase_s: float = 1.0  # duration of X
    default_tempo: str = "2010"
    reps_compound: int = 8
    reps_isolation: int = 12
    warmup_scheme: tuple[tuple[float, int], ...] = ((0.4, 8), (0.6, 5), (0.8, 3))
    warmup_set_rest_s: int = 60

    # Progression and deload
    weekly_volume_increase: float = 0.15
    max_sets_per_exercise: int = 5
    rir_start: int = 3
    rir_end: int = 1
    deload_volume_factor: float = 0.5
    deload_rir: int = 4

    def weight(self, role: Role) -> float:
        """Effective-set weight of a role; a role missing from the config counts as 0."""
        return self.role_weights.get(role, 0.0)


# ---------------------------------------------------------------------------
# Plans
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PlannedExercise:
    exercise: ExerciseSpec
    sets: int

    def __post_init__(self) -> None:
        if self.sets < 1:
            raise ValueError(f"sets must be >= 1, got {self.sets}")


@dataclass(frozen=True, slots=True)
class Session:
    """One workout. Exercise order matters (warm-up sets, transitions)."""

    exercises: tuple[PlannedExercise, ...]
    max_minutes: int


@dataclass(frozen=True, slots=True)
class Week:
    sessions: tuple[Session, ...]
    rir: int
    is_deload: bool = False


@dataclass(frozen=True, slots=True)
class Mesocycle:
    weeks: tuple[Week, ...] = field(default_factory=tuple)

    @property
    def training_weeks(self) -> tuple[Week, ...]:
        """Weeks that count towards the objective (all except deload)."""
        return tuple(w for w in self.weeks if not w.is_deload)
