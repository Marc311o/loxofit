"""The fast objective must give the same score as the reference evaluate_plan."""

import random

import pytest

from app.engine.evaluate import evaluate_plan
from app.engine.objective import Objective
from app.engine.types import EngineConfig, ExerciseSpec, MuscleTarget, Role
from tests.engine.samples import BENCH, CAPPED, CLOSE_GRIP, CURL, FLY, RESTED, ROW

MUSCLES = ["pec_major", "delt_ant", "delt_mid", "triceps", "lats", "biceps", "quads", "glute_max"]
TEMPOS = [None, "2010", "3010", "X0X0", "4121", "20X1"]


def random_exercise(rng: random.Random, i: int) -> ExerciseSpec:
    muscles = rng.sample(MUSCLES, rng.randint(1, 4))
    roles = {m: rng.choice(list(Role)) for m in muscles}
    roles[muscles[0]] = Role.PRIMARY  # every exercise trains something
    return ExerciseSpec(
        code=f"ex{i}",
        is_compound=rng.random() < 0.6,
        muscle_roles=roles,
        tempo=rng.choice(TEMPOS),
        is_unilateral=rng.random() < 0.2,
    )


def random_targets(rng: random.Random) -> dict[str, MuscleTarget]:
    targets = {}
    for m in rng.sample(MUSCLES, rng.randint(1, len(MUSCLES))):
        mev = rng.uniform(0, 8)
        mav = mev + rng.uniform(1, 10)
        mrv = mav + rng.uniform(0, 6)
        targets[m] = MuscleTarget(mev, mav, mrv, priority=rng.choice([0, 0.5, 1, 1, 2]))
    return targets


def random_config(rng: random.Random) -> EngineConfig:
    return EngineConfig(
        role_weights={Role.PRIMARY: 1.0, Role.SECONDARY: rng.choice([0.0, 0.5, 1.0])},
        curve_k=rng.uniform(1, 5),
        penalty_lambda=rng.uniform(0, 0.2),
        time_penalty=rng.uniform(0, 0.5),
        session_volume_cap=rng.choice([None, 4.0, 11.0]),
        rest_before_next_exercise=rng.random() < 0.5,
        transitions_s=rng.choice([30, 60, 90]),
        weekly_volume_increase=rng.uniform(0, 0.3),
        max_sets_per_exercise=rng.randint(3, 8),
    )


def random_candidate(rng: random.Random, n_exercises: int, n_sessions: int) -> list[list[tuple]]:
    return [
        [
            (i, rng.randint(1, 8))
            for i in rng.sample(range(n_exercises), rng.randint(0, min(7, n_exercises)))
        ]
        for _ in range(n_sessions)
    ]


@pytest.mark.parametrize("seed", range(300))
def test_matches_reference_on_random_plans(seed):
    rng = random.Random(seed)
    exercises = [random_exercise(rng, i) for i in range(rng.randint(1, 12))]
    targets = random_targets(rng)
    config = random_config(rng)
    weeks = rng.randint(2, 8)
    limits = [rng.choice([15, 30, 45, 60, 90]) for _ in range(rng.randint(1, 6))]
    objective = Objective(exercises, targets, config, weeks, limits)

    for _ in range(5):
        candidate = random_candidate(rng, len(exercises), len(limits))
        expected = evaluate_plan(objective.to_sessions(candidate), weeks, targets, config).score
        assert objective.score(candidate) == pytest.approx(expected, rel=1e-9, abs=1e-9)


@pytest.mark.parametrize("config", [CAPPED, RESTED], ids=["per-muscle-v1", "per-muscle-v2"])
def test_matches_reference_on_the_shared_catalog(config):
    exercises = [BENCH, ROW, FLY, CURL, CLOSE_GRIP]
    targets = {m: MuscleTarget(4, 13, 16) for m in ("pec_major", "lats", "biceps", "triceps")}
    objective = Objective(exercises, targets, config, 5, [60, 45])
    candidate = [[(0, 4), (4, 6), (2, 3)], [(1, 4), (3, 3), (0, 2)]]  # chest over the cap
    expected = evaluate_plan(objective.to_sessions(candidate), 5, targets, config).score
    assert objective.score(candidate) == pytest.approx(expected, rel=1e-12)


def test_scoring_does_not_depend_on_the_cache():
    # The same candidate twice: the second call runs on cached genes.
    exercises = [BENCH, ROW]
    targets = {"pec_major": MuscleTarget(4, 13, 16)}
    objective = Objective(exercises, targets, CAPPED, 4, [60])
    candidate = [[(0, 3), (1, 3)]]
    assert objective.score(candidate) == objective.score(candidate)


def test_sets_per_week_follow_the_progression():
    objective = Objective([BENCH], {}, CAPPED, 5, [60])
    # +15% a week, capped at 5, then the deload halves the base: 3 -> 3, 3, 4, 5 | 2
    assert objective.sets_per_week(3) == (3, 3, 4, 5, 2)
