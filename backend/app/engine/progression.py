"""From a base week to a full mesocycle.

Training weeks 1..T:
    sets_w = round(base_sets * (1 + increase)^(w-1)), capped at max_sets_per_exercise
    RIR goes linearly from rir_start (week 1) to rir_end (week T)
Last week is a deload:
    sets = max(1, round(base_sets * deload_volume_factor)), RIR = deload_rir
"""

import math
from dataclasses import replace

from app.engine.types import EngineConfig, Mesocycle, Session, Week


def round_half_up(x: float) -> int:
    return math.floor(x + 0.5)


def progressed_sets(base: int, week: int, config: EngineConfig) -> int:
    """Sets in training week `week` (1-based). Never fewer than in week 1."""
    grown = base * (1 + config.weekly_volume_increase) ** (week - 1)
    cap = max(base, config.max_sets_per_exercise)
    return min(round_half_up(grown), cap)


def deload_sets(base: int, config: EngineConfig) -> int:
    return max(1, round_half_up(base * config.deload_volume_factor))


def rir_for_week(week: int, training_weeks: int, config: EngineConfig) -> int:
    if training_weeks == 1:
        return config.rir_start
    step = (config.rir_end - config.rir_start) / (training_weeks - 1)
    return round_half_up(config.rir_start + step * (week - 1))


def _progressed_session(base: Session, week: int, config: EngineConfig) -> Session:
    exercises = tuple(
        replace(p, sets=progressed_sets(p.sets, week, config)) for p in base.exercises
    )
    return replace(base, exercises=exercises)


def _deload_session(base: Session, config: EngineConfig) -> Session:
    exercises = tuple(replace(p, sets=deload_sets(p.sets, config)) for p in base.exercises)
    return replace(base, exercises=exercises)


def build_mesocycle(base_week: tuple[Session, ...], weeks: int, config: EngineConfig) -> Mesocycle:
    """`weeks - 1` progressive training weeks followed by one deload week."""
    if weeks < 2:
        raise ValueError(f"A mesocycle needs at least 2 weeks (training + deload), got {weeks}")
    training_weeks = weeks - 1

    result = [
        Week(
            sessions=tuple(_progressed_session(s, w, config) for s in base_week),
            rir=rir_for_week(w, training_weeks, config),
        )
        for w in range(1, training_weeks + 1)
    ]
    result.append(
        Week(
            sessions=tuple(_deload_session(s, config) for s in base_week),
            rir=config.deload_rir,
            is_deload=True,
        )
    )
    return Mesocycle(tuple(result))
