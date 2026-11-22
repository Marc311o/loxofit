"""
Plan generation: a training problem in, the best base week found out.

`build_search` turns the catalog exercises the user can do, the session focuses
and limits into the objective and the search space - the same way for the app and
for the experiments. `generate` runs the optimizer chosen by the experiments: hill
climbing, which was never significantly worse than the genetic and memetic
algorithms, sometimes better, and the fastest (research/experiments).

Everything here is plain data, so a GenerationTask can be sent to another process.
"""

import random
from collections.abc import Sequence
from dataclasses import dataclass

from app.engine.focus import Focus, session_pools
from app.engine.objective import Objective
from app.engine.optimizers import ProgressCallback, hill_climbing
from app.engine.space import SearchSpace, recommended_rank
from app.engine.types import EngineConfig, ExerciseSpec, MuscleTargets

# Tuned on the TUNE scenarios (research/experiments): the lowest mean rank of 200-2000.
PATIENCE = 1000
BUDGET = 30_000
MAX_PER_PATTERN = 1  # one exercise of a movement pattern per session


@dataclass(frozen=True)
class CandidateExercise:
    """A catalog exercise the generator may use, with what ordering and variety need."""

    spec: ExerciseSpec
    complexity: int
    fatigue_cost: int
    movement_pattern: str


@dataclass(frozen=True)
class GenerationTask:
    exercises: tuple[CandidateExercise, ...]
    focuses: tuple[Focus, ...]
    session_minutes: tuple[int, ...]
    targets: MuscleTargets
    config: EngineConfig
    weeks: int
    seed: int
    budget: int = BUDGET
    patience: int = PATIENCE


@dataclass(frozen=True)
class GenerationResult:
    sessions: tuple[tuple[tuple[int, int], ...], ...]  # (exercise index, base sets), in order
    score: float
    max_score: float
    evaluations: int
    history: tuple[tuple[int, float], ...]  # (evaluations, best score) at every improvement


class EmptySessionError(ValueError):
    """No exercise fits a session (its focus, with the available equipment)."""

    def __init__(self, session: int) -> None:
        self.session = session
        super().__init__(f"No exercise fits session {session + 1}")


def build_search(
    exercises: Sequence[CandidateExercise],
    focuses: Sequence[Focus],
    session_minutes: Sequence[int],
    targets: MuscleTargets,
    config: EngineConfig,
    weeks: int,
) -> tuple[Objective, SearchSpace]:
    specs = tuple(e.spec for e in exercises)
    pools = session_pools(specs, focuses)
    for s, pool in enumerate(pools):
        if not pool:
            raise EmptySessionError(s)
    space = SearchSpace(
        specs,
        pools=pools,
        rank=recommended_rank(
            specs,
            complexity=[e.complexity for e in exercises],
            fatigue_cost=[e.fatigue_cost for e in exercises],
        ),
        patterns=tuple(e.movement_pattern for e in exercises),
        max_per_pattern=MAX_PER_PATTERN,
    )
    objective = Objective(specs, targets, config, weeks, session_minutes)
    return objective, space


def generate(task: GenerationTask, on_progress: ProgressCallback | None = None) -> GenerationResult:
    objective, space = build_search(
        task.exercises, task.focuses, task.session_minutes, task.targets, task.config, task.weeks
    )
    result = hill_climbing(
        objective, space, task.budget, random.Random(task.seed), on_progress, task.patience
    )
    return GenerationResult(
        sessions=result.best,
        score=result.score,
        max_score=objective.max_score,
        evaluations=result.evaluations,
        history=tuple(result.history),
    )
