from collections import defaultdict
from collections.abc import Iterable

from app.engine.types import EngineConfig, PlannedExercise, Session

Volume = dict[str, float]  # muscle code -> effective sets


def exercise_volume(planned: PlannedExercise, config: EngineConfig) -> Volume:
    """Effective sets contributed by one planned exercise. Zero-weight roles are skipped."""
    volume: Volume = {}
    for muscle, role in planned.exercise.muscle_roles.items():
        weight = config.weight(role)
        if weight > 0:
            volume[muscle] = planned.sets * weight
    return volume


def weekly_volume(sessions: Iterable[Session], config: EngineConfig) -> Volume:
    """
    Effective sets per muscle summed over all sessions of a week.
    Muscles that receive no volume are absent from the result
    """
    total: defaultdict[str, float] = defaultdict(float)
    for session in sessions:
        for planned in session.exercises:
            for muscle, sets in exercise_volume(planned, config).items():
                total[muscle] += sets
    return dict(total)


def effective_volume(sessions: Iterable[Session], config: EngineConfig) -> Volume:
    """
    Weekly volume that counts towards the benefit: in every session a muscle
    contributes at most `session_volume_cap` sets. Sets above the cap add fatigue
    and time, but no growth - so they still count for MRV and session length.
    """
    cap = config.session_volume_cap
    total: defaultdict[str, float] = defaultdict(float)
    for session in sessions:
        for muscle, sets in weekly_volume([session], config).items():
            total[muscle] += sets if cap is None else min(sets, cap)
    return dict(total)
