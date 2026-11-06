"""Plan data -> engine types, and engine results -> API schemas."""

from collections.abc import Iterable, Mapping
from dataclasses import fields

from app.domains.catalog.schemas import ExerciseRoles, MuscleRead
from app.domains.model_config.enums import VolumeMode
from app.domains.model_config.models import ModelConfig
from app.domains.plans.enums import AnalysisSource, VolumeZone
from app.domains.plans.exceptions import UnsupportedConfigError
from app.domains.plans.models import PlanSession, PlanWeek
from app.domains.plans.schemas import MuscleAnalysis, PlanAnalysis, WeekAnalysis
from app.engine.evaluate import Evaluation
from app.engine.types import (
    EngineConfig,
    ExerciseSpec,
    Mesocycle,
    MuscleTarget,
    MuscleTargets,
    PlannedExercise,
    Role,
    Session,
    Week,
)

_ENGINE_FIELDS = frozenset(f.name for f in fields(EngineConfig)) - {"role_weights"}


def build_config(config: ModelConfig) -> EngineConfig:
    """Role weights plus every parameter present in both ModelConfig and EngineConfig."""
    params = {name: getattr(config, name) for name in _ENGINE_FIELDS if hasattr(config, name)}
    weights = {Role(rw.role.value): rw.weight for rw in config.role_weights}
    return EngineConfig(role_weights=weights, **params)


def build_targets(
    config: ModelConfig, muscles: Iterable[MuscleRead], priorities: Mapping[int, float]
) -> MuscleTargets:
    """Global mode: every volume-target muscle gets the same landmarks."""
    if config.volume_mode != VolumeMode.GLOBAL:
        raise UnsupportedConfigError(f"Volume mode {config.volume_mode!r} is not supported yet")
    mev, mav, mrv = config.global_mev, config.global_mav_upper, config.global_mrv
    if mev is None or mav is None or mrv is None:
        raise UnsupportedConfigError(f"Config {config.name!r} has no global landmarks")
    return {
        m.code: MuscleTarget(mev=mev, mav_upper=mav, mrv=mrv, priority=priorities.get(m.id, 1.0))
        for m in muscles
        if m.is_volume_target
    }


def build_spec(exercise: ExerciseRoles) -> ExerciseSpec:
    return ExerciseSpec(
        code=exercise.code,
        is_compound=exercise.is_compound,
        muscle_roles={muscle: Role(role.value) for muscle, role in exercise.roles.items()},
        tempo=exercise.default_tempo,
        is_unilateral=exercise.is_unilateral,
    )


def build_session(session: PlanSession, specs: Mapping[int, ExerciseSpec]) -> Session:
    return Session(
        exercises=tuple(PlannedExercise(specs[e.exercise_id], e.sets) for e in session.exercises),
        max_minutes=session.max_minutes,
    )


def build_week(week: PlanWeek, specs: Mapping[int, ExerciseSpec]) -> Week:
    return Week(
        sessions=tuple(build_session(s, specs) for s in week.sessions),
        rir=week.rir,
        is_deload=week.is_deload,
    )


def volume_zone(volume: float, target: MuscleTarget) -> VolumeZone:
    if volume < target.mev:
        return VolumeZone.BELOW_MEV
    if volume < target.mav_upper:
        return VolumeZone.MEV_MAV
    if volume <= target.mrv:
        return VolumeZone.MAV_MRV
    return VolumeZone.ABOVE_MRV


def _r(x: float) -> float:
    return round(x, 2)


def to_analysis(
    mesocycle: Mesocycle,
    evaluation: Evaluation,
    targets: MuscleTargets,
    muscle_ids: Mapping[str, int],
    source: AnalysisSource,
) -> PlanAnalysis:
    weeks = []
    for number, (week, ev) in enumerate(
        zip(mesocycle.weeks, evaluation.weeks, strict=True), start=1
    ):
        muscles = []
        for code, target in targets.items():
            volume = ev.volume.get(code, 0.0)
            score = ev.muscles.get(code)
            muscles.append(
                MuscleAnalysis(
                    muscle_id=muscle_ids[code],
                    muscle_code=code,
                    volume=_r(volume),
                    zone=volume_zone(volume, target),
                    benefit=_r(score.benefit) if score else None,
                    penalty=_r(score.penalty) if score else None,
                    score=_r(score.score) if score else None,
                )
            )
        weeks.append(
            WeekAnalysis(
                week_number=number,
                rir=week.rir,
                is_deload=week.is_deload,
                volume_score=_r(ev.volume_score),
                overtime_minutes=_r(ev.overtime_minutes),
                session_minutes=[_r(m) for m in ev.session_minutes],
                muscles=muscles,
            )
        )
    return PlanAnalysis(
        source=source,
        score=_r(evaluation.score),
        volume_score=_r(evaluation.volume_score),
        time_penalty=_r(evaluation.time_penalty),
        weeks=weeks,
    )
