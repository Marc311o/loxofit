"""
Evaluates a training plan with the engine - no server, no database.

Usage:
    python -m app.scripts.engine_eval data/plans/example_upper_lower.json
    python -m app.scripts.engine_eval PLAN [--config NAME] [--weeks N] [--catalog XLSX] [--json]

The plan file describes ONE base week; the engine progresses it into a mesocycle
(weeks - 1 training weeks + deload) and prints volume, benefit and session times:

    {
      "weeks": 5,
      "sessions": [
        {"name": "Upper A", "max_minutes": 60,
         "exercises": [{"exercise": "bb_bench", "sets": 3}, ...]}
      ]
    }

Exercises are referenced by their catalog `code`. Muscle roles and tempo come from the
catalog spreadsheet, the model parameters from config_versions.CONFIGS.
"""

import argparse
import json
import sys
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.domains.model_config.enums import VolumeMode
from app.engine.evaluate import Evaluation, evaluate
from app.engine.progression import build_mesocycle
from app.engine.types import (
    EngineConfig,
    ExerciseSpec,
    Mesocycle,
    MuscleTarget,
    MuscleTargets,
    PlannedExercise,
    Role,
    Session,
)
from app.scripts.catalog_file import DATA_FILE, CatalogData, SeedDataError, load_catalog
from app.scripts.config_versions import DEFAULT_CONFIG_NAME, ConfigVersion, get_config


class PlanError(Exception):
    """The plan file is invalid. Carries every problem found, not just the first."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__(f"{len(errors)} errors found in plan")


# ---------------------------------------------------------------------------
# Plan file
# ---------------------------------------------------------------------------


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ExerciseEntry(_Strict):
    exercise: str
    sets: int = Field(ge=1)


class SessionEntry(_Strict):
    name: str = Field(min_length=1)
    max_minutes: int = Field(ge=1)
    exercises: list[ExerciseEntry] = Field(min_length=1)


class PlanFile(_Strict):
    weeks: int = Field(default=5, ge=2)
    sessions: list[SessionEntry] = Field(min_length=1)


def read_plan(path: Path) -> PlanFile:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PlanError([f"File {path} not found"]) from exc
    except json.JSONDecodeError as exc:
        raise PlanError([f"{path}: invalid JSON ({exc})"]) from exc

    try:
        return PlanFile.model_validate(raw)
    except ValidationError as exc:
        errors = []
        for err in exc.errors():
            location = ".".join(str(part) for part in err["loc"])
            errors.append(f"{location}: {err['msg']}")
        raise PlanError(errors) from exc


# ---------------------------------------------------------------------------
# Catalog and config -> engine types (a minimal adapter; the real one comes in S3)
# ---------------------------------------------------------------------------


def build_specs(catalog: CatalogData) -> dict[str, ExerciseSpec]:
    """Exercise code -> ExerciseSpec with muscle roles from the spreadsheet."""
    roles: dict[str, dict[str, Role]] = {e.code: {} for e in catalog.exercises}
    for r in catalog.roles:
        roles[r.exercise][r.muscle] = Role(r.role.value)
    return {
        e.code: ExerciseSpec(
            code=e.code,
            is_compound=e.is_compound,
            muscle_roles=roles[e.code],
            tempo=e.default_tempo,
            is_unilateral=e.is_unilateral,
        )
        for e in catalog.exercises
    }


_ENGINE_FIELDS = {f.name for f in fields(EngineConfig)} - {"role_weights"}


def build_config(version: ConfigVersion) -> EngineConfig:
    """Role weights plus every config parameter the engine knows; the rest keeps defaults."""
    params = {k: v for k, v in version.params.items() if k in _ENGINE_FIELDS}
    weights = {Role(role.value): weight for role, weight in version.role_weights.items()}
    return EngineConfig(role_weights=weights, **params)


def build_targets(version: ConfigVersion, catalog: CatalogData) -> MuscleTargets:
    """Global mode: every volume-target muscle gets the same landmarks."""
    mode = version.params.get("volume_mode", VolumeMode.GLOBAL)
    if mode != VolumeMode.GLOBAL:
        raise PlanError([f"Config {version.name!r}: volume mode {mode!r} is not supported yet"])
    target = MuscleTarget(
        mev=version.params["global_mev"],
        mav_upper=version.params["global_mav_upper"],
        mrv=version.params["global_mrv"],
    )
    return {m.code: target for m in catalog.muscles if m.is_volume_target}


def build_base_week(plan: PlanFile, specs: dict[str, ExerciseSpec]) -> tuple[Session, ...]:
    unknown = [
        f"sessions.{i}.exercises.{j}.exercise: unknown code {entry.exercise!r}"
        for i, session in enumerate(plan.sessions)
        for j, entry in enumerate(session.exercises)
        if entry.exercise not in specs
    ]
    if unknown:
        raise PlanError(unknown)

    return tuple(
        Session(
            exercises=tuple(PlannedExercise(specs[e.exercise], e.sets) for e in s.exercises),
            max_minutes=s.max_minutes,
        )
        for s in plan.sessions
    )


# ---------------------------------------------------------------------------
# Running and reporting
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Run:
    plan: PlanFile
    config_name: str
    targets: MuscleTargets
    mesocycle: Mesocycle
    evaluation: Evaluation


def run(
    plan_path: Path,
    config_name: str = DEFAULT_CONFIG_NAME,
    weeks: int | None = None,
    catalog_path: Path = DATA_FILE,
) -> Run:
    plan = read_plan(plan_path)
    if weeks is not None:
        if weeks < 2:
            raise PlanError([f"--weeks must be at least 2, got {weeks}"])
        plan = plan.model_copy(update={"weeks": weeks})

    catalog = load_catalog(catalog_path)
    version = get_config(config_name)
    config = build_config(version)
    targets = build_targets(version, catalog)
    base_week = build_base_week(plan, build_specs(catalog))

    mesocycle = build_mesocycle(base_week, plan.weeks, config)
    return Run(plan, config_name, targets, mesocycle, evaluate(mesocycle, targets, config))


def zone(volume: float, target: MuscleTarget) -> str:
    if volume < target.mev:
        return "< MEV"
    if volume <= target.mav_upper:
        return "MEV-MAV"
    if volume <= target.mrv:
        return "MAV-MRV"
    return "> MRV"


def _muscle_table(result: Run, week_index: int) -> list[str]:
    evaluation = result.evaluation.weeks[week_index]
    header = f"  {'muscle':<10} {'sets':>6}  {'zone':<8} {'benefit':>8} {'penalty':>8} {'score':>7}"
    lines = [header]
    for muscle, s in sorted(evaluation.muscles.items(), key=lambda kv: -kv[1].volume):
        lines.append(
            f"  {muscle:<10} {s.volume:>6.1f}  {zone(s.volume, result.targets[muscle]):<8}"
            f" {s.benefit:>8.2f} {s.penalty:>8.2f} {s.score:>7.2f}"
        )
    return lines


def format_report(result: Run) -> str:
    plan, meso, ev = result.plan, result.mesocycle, result.evaluation
    any_target = next(iter(result.targets.values()))
    lines = [
        f"Config: {result.config_name}  (MEV {any_target.mev:g}, MAV {any_target.mav_upper:g},"
        f" MRV {any_target.mrv:g} effective sets / week)",
        f"Mesocycle: {plan.weeks - 1} training weeks + deload",
        "",
        "Base week",
    ]
    for session in plan.sessions:
        items = ", ".join(f"{e.exercise} x{e.sets}" for e in session.exercises)
        lines.append(f"  {session.name} ({session.max_minutes} min): {items}")

    lines += ["", "Weeks"]
    for i, (week, week_ev) in enumerate(zip(meso.weeks, ev.weeks, strict=True), start=1):
        label = "deload" if week.is_deload else f"week {i}"
        times = []
        for session, minutes in zip(plan.sessions, week_ev.session_minutes, strict=True):
            over = minutes - session.max_minutes
            overtime = f" (+{over:.0f})" if over > 0 else ""
            times.append(f"{session.name} {minutes:.0f} min{overtime}")
        lines.append(
            f"  {label:<7} RIR {week.rir}  score {week_ev.volume_score:6.2f}  | " + ", ".join(times)
        )

    last_training = len(meso.weeks) - 2
    lines += ["", "Muscles - week 1", *_muscle_table(result, 0)]
    if last_training > 0:
        lines += ["", f"Muscles - week {last_training + 1}", *_muscle_table(result, last_training)]

    lines += [
        "",
        f"Volume score {ev.volume_score:.2f} - time penalty {ev.time_penalty:.2f}"
        f" = SCORE {ev.score:.2f}",
    ]
    return "\n".join(lines)


def to_json(result: Run) -> dict[str, Any]:
    """Machine-readable result - for experiments and for tables in the thesis."""
    ev = result.evaluation
    return {
        "config": result.config_name,
        "weeks": result.plan.weeks,
        "score": ev.score,
        "volume_score": ev.volume_score,
        "time_penalty": ev.time_penalty,
        "per_week": [
            {
                "rir": week.rir,
                "is_deload": week.is_deload,
                "volume_score": week_ev.volume_score,
                "session_minutes": list(week_ev.session_minutes),
                "overtime_minutes": week_ev.overtime_minutes,
                "volume": week_ev.volume,
                "muscles": {
                    m: {
                        "volume": s.volume,
                        "benefit": s.benefit,
                        "penalty": s.penalty,
                        "score": s.score,
                    }
                    for m, s in week_ev.muscles.items()
                },
            }
            for week, week_ev in zip(result.mesocycle.weeks, ev.weeks, strict=True)
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate a training plan with the engine.")
    parser.add_argument("plan", type=Path, help="plan file (JSON)")
    parser.add_argument("--config", default=DEFAULT_CONFIG_NAME, help="config name")
    parser.add_argument("--weeks", type=int, help="override mesocycle length (with deload)")
    parser.add_argument("--catalog", type=Path, default=DATA_FILE, help="catalog spreadsheet")
    parser.add_argument("--json", action="store_true", help="print JSON instead of a report")
    args = parser.parse_args(argv)

    try:
        result = run(args.plan, args.config, args.weeks, args.catalog)
    except (PlanError, SeedDataError) as exc:
        print(f"Error - {len(exc.errors)} problem(s):", file=sys.stderr)
        for error in exc.errors:
            print(f"  {error}", file=sys.stderr)
        return 1
    except KeyError as exc:
        print(f"Error: {exc.args[0]}", file=sys.stderr)
        return 1

    print(json.dumps(to_json(result), indent=2) if args.json else format_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
