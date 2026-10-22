from collections.abc import Iterable

from app.engine.types import EngineConfig, ExerciseSpec, PlannedExercise, Session

_EXPLOSIVE = {"0", "X"}


def rep_duration_s(tempo: str, explosive_phase_s: float) -> float:
    """Seconds per rep from a 4-character tempo: eccentric, bottom, concentric, top."""
    tempo = tempo.upper()
    if len(tempo) != 4 or any(c not in "0123456789X" for c in tempo):
        raise ValueError(f"Invalid tempo {tempo!r}, expected 4 characters of 0-9 or X")
    if tempo[1] == "X" or tempo[3] == "X":
        raise ValueError(f"Invalid tempo {tempo!r}: X is allowed only for movement phases")

    total = 0.0
    for i, c in enumerate(tempo):
        is_movement = i in (0, 2)
        total += explosive_phase_s if is_movement and c in _EXPLOSIVE else int(c)
    return total


def set_duration_s(exercise: ExerciseSpec, reps: int, config: EngineConfig) -> float:
    per_rep = rep_duration_s(exercise.tempo or config.default_tempo, config.explosive_phase_s)
    sides = 2 if exercise.is_unilateral else 1
    return reps * per_rep * sides


def working_reps(exercise: ExerciseSpec, config: EngineConfig) -> int:
    return config.reps_compound if exercise.is_compound else config.reps_isolation


def warmup_duration_s(exercise: ExerciseSpec, config: EngineConfig) -> float:
    """Ramp-up sets from config.warmup_scheme, each followed by a short rest."""
    return sum(
        set_duration_s(exercise, reps, config) + config.warmup_set_rest_s
        for _, reps in config.warmup_scheme
    )


def needs_warmup(exercise: ExerciseSpec, trained_primary: set[str]) -> bool:
    """Compound whose primary muscles were not yet trained as primary in this session."""
    return exercise.is_compound and trained_primary.isdisjoint(exercise.primary_muscles())


def exercise_duration_s(planned: PlannedExercise, config: EngineConfig, warm_up: bool) -> float:
    exercise = planned.exercise
    rest = config.rest_compound_s if exercise.is_compound else config.rest_isolation_s
    working = planned.sets * set_duration_s(exercise, working_reps(exercise, config), config)
    rests = (planned.sets - 1) * rest
    return working + rests + (warmup_duration_s(exercise, config) if warm_up else 0.0)


def session_duration_s(session: Session, config: EngineConfig) -> float:
    total = float(config.warmup_s)
    trained_primary: set[str] = set()
    for planned in session.exercises:
        warm_up = needs_warmup(planned.exercise, trained_primary)
        total += exercise_duration_s(planned, config, warm_up)
        trained_primary |= planned.exercise.primary_muscles()
    total += max(0, len(session.exercises) - 1) * config.transitions_s
    return total


def overtime_minutes(session: Session, config: EngineConfig) -> float:
    """Minutes over the session limit (0 if within)."""
    return max(0.0, session_duration_s(session, config) / 60 - session.max_minutes)


def total_overtime_minutes(sessions: Iterable[Session], config: EngineConfig) -> float:
    return sum(overtime_minutes(s, config) for s in sessions)
