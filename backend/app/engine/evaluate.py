"""
Objective function of a mesocycle - the single number the optimizer maximizes.
"""

from dataclasses import dataclass

from app.engine.benefit import MuscleScore, score_muscles
from app.engine.progression import build_mesocycle
from app.engine.timing import overtime_minutes, session_duration_s
from app.engine.types import EngineConfig, Mesocycle, MuscleTargets, Session, Week
from app.engine.volume import Volume, weekly_volume


@dataclass(frozen=True, slots=True)
class WeekEvaluation:
    volume: Volume
    muscles: dict[str, MuscleScore]  # empty for the deload week
    volume_score: float  # 0 for the deload week
    session_minutes: tuple[float, ...]
    overtime_minutes: float


@dataclass(frozen=True, slots=True)
class Evaluation:
    score: float
    volume_score: float
    time_penalty: float
    weeks: tuple[WeekEvaluation, ...]


def _evaluate_week(week: Week, targets: MuscleTargets, config: EngineConfig) -> WeekEvaluation:
    volume = weekly_volume(week.sessions, config)
    muscles = {} if week.is_deload else score_muscles(volume, targets, config)
    return WeekEvaluation(
        volume=volume,
        muscles=muscles,
        volume_score=sum(m.score for m in muscles.values()),
        session_minutes=tuple(session_duration_s(s, config) / 60 for s in week.sessions),
        overtime_minutes=sum(overtime_minutes(s, config) for s in week.sessions),
    )


def evaluate(mesocycle: Mesocycle, targets: MuscleTargets, config: EngineConfig) -> Evaluation:
    weeks = tuple(_evaluate_week(w, targets, config) for w in mesocycle.weeks)
    volume_score = sum(w.volume_score for w in weeks)
    time_penalty = config.time_penalty * sum(w.overtime_minutes for w in weeks)
    return Evaluation(volume_score - time_penalty, volume_score, time_penalty, weeks)


def evaluate_plan(
    base_week: tuple[Session, ...], weeks: int, targets: MuscleTargets, config: EngineConfig
) -> Evaluation:
    """Fitness of a base week: progress it into a mesocycle and evaluate that."""
    return evaluate(build_mesocycle(base_week, weeks, config), targets, config)
