"""Optimizers: budget, validity, reproducibility - and finding the optimum of a tiny problem."""

import itertools
import random
from functools import partial

import pytest

from app.engine.objective import Objective
from app.engine.optimizers import (
    GeneticParams,
    Progress,
    genetic,
    greedy,
    hill_climbing,
    memetic,
    random_search,
)
from app.engine.space import SearchSpace
from app.engine.types import MuscleTarget
from tests.engine.samples import BENCH, CLOSE_GRIP, CONFIG, CURL, FLY, ROW, SHOULDER_PRESS

EXERCISES = (BENCH, ROW, FLY, CURL, SHOULDER_PRESS, CLOSE_GRIP)
MUSCLES = ("pec_major", "lats", "biceps", "triceps", "delt_ant")
TARGETS = {m: MuscleTarget(4, 13, 16) for m in MUSCLES}
OBJECTIVE = Objective(EXERCISES, TARGETS, CONFIG, weeks=5, session_limits=[60, 60, 60])
SPACE = SearchSpace(
    EXERCISES,
    pools=((0, 2, 4, 5), (1, 3), (0, 1, 2, 3, 4, 5)),  # push, pull, full body
    rank=(0, 2, 4, 5, 1, 3),
    max_exercises=4,
)
TINY = SearchSpace((BENCH, ROW, CURL), pools=((0, 1, 2), (0, 1, 2)), rank=(0, 1, 2),
                   min_sets=1, max_sets=3, max_exercises=2)  # fmt: skip

OPTIMIZERS = {
    "random_search": random_search,
    "greedy": greedy,
    "hill_climbing": hill_climbing,
    "genetic_session": genetic,
    "genetic_gene": partial(genetic, params=GeneticParams(crossover="gene")),
    "memetic": memetic,
}


@pytest.mark.parametrize("name", OPTIMIZERS)
def test_stays_within_budget_and_returns_a_valid_plan(name):
    result = OPTIMIZERS[name](OBJECTIVE, SPACE, 3000, random.Random(0))
    assert result.evaluations <= 3000
    assert SPACE.is_valid(result.best)
    assert result.score == pytest.approx(OBJECTIVE.score(result.best))


@pytest.mark.parametrize("name", OPTIMIZERS)
def test_same_seed_same_result(name):
    first = OPTIMIZERS[name](OBJECTIVE, SPACE, 2000, random.Random(7))
    second = OPTIMIZERS[name](OBJECTIVE, SPACE, 2000, random.Random(7))
    assert first == second


@pytest.mark.parametrize("name", ["random_search", "hill_climbing", "genetic_session", "memetic"])
def test_history_only_improves(name):
    result = OPTIMIZERS[name](OBJECTIVE, SPACE, 3000, random.Random(1))
    evaluations = [e for e, _ in result.history]
    scores = [s for _, s in result.history]
    assert evaluations == sorted(evaluations)
    assert scores == sorted(scores) and len(set(scores)) == len(scores)
    assert scores[-1] == result.score


def test_search_beats_random_sampling():
    # Same budget: guided search should not lose to blind sampling.
    budget = 5000
    baseline = random_search(OBJECTIVE, SPACE, budget, random.Random(3)).score
    assert hill_climbing(OBJECTIVE, SPACE, budget, random.Random(3)).score >= baseline
    assert genetic(OBJECTIVE, SPACE, budget, random.Random(3)).score >= baseline
    assert memetic(OBJECTIVE, SPACE, budget, random.Random(3)).score >= baseline


def test_progress_is_reported():
    seen: list[Progress] = []
    random_search(OBJECTIVE, SPACE, 1200, random.Random(0), on_progress=seen.append)
    assert [p.evaluations for p in seen] == [500, 1000, 1200]  # the last one at the end
    assert all(p.budget == 1200 for p in seen)


def test_greedy_is_deterministic_and_may_stop_early():
    result = greedy(OBJECTIVE, SPACE, 100_000)
    assert result.evaluations < 100_000  # reached a local optimum on its own
    assert result == greedy(OBJECTIVE, SPACE, 100_000, random.Random(123))


# -- a problem small enough to solve exhaustively -----------------------------------------

TINY_OBJECTIVE = Objective(
    (BENCH, ROW, CURL), {m: MuscleTarget(2, 6, 8) for m in ("pec_major", "lats", "biceps")},
    CONFIG, weeks=3, session_limits=[45, 45],
)  # fmt: skip
TINY = SearchSpace((BENCH, ROW, CURL), pools=((0, 1, 2), (0, 1, 2)), rank=(0, 1, 2),
                   max_sets=3, max_exercises=2)  # fmt: skip


def all_sessions(space: SearchSpace, s: int):
    for k in range(1, space.max_exercises + 1):
        for exercises in itertools.combinations(space.pools[s], k):
            for sets in itertools.product(range(space.min_sets, space.max_sets + 1), repeat=k):
                yield space.ordered(zip(exercises, sets, strict=True))


def test_tiny_problem_optimum_is_found():
    # 2 sessions x 36 options = 1296 candidates; the best one by brute force.
    optimum = max(
        TINY_OBJECTIVE.score(c)
        for c in itertools.product(all_sessions(TINY, 0), all_sessions(TINY, 1))
    )
    for optimizer in (hill_climbing, genetic, memetic):
        result = optimizer(TINY_OBJECTIVE, TINY, 3000, random.Random(0))
        assert result.score == pytest.approx(optimum)
    assert greedy(TINY_OBJECTIVE, TINY, 3000).score <= optimum + 1e-9


def test_invalid_genetic_params_are_rejected():
    with pytest.raises(ValueError):
        GeneticParams(population=10, tournament=11)
    with pytest.raises(ValueError):
        GeneticParams(mutation_rate=1.0)
    with pytest.raises(ValueError):
        GeneticParams(population=10, local_search_count=11)


def test_plain_genetic_does_no_local_search():
    # With local_search_count = 0 the memetic code path must not change anything.
    explicit = GeneticParams(local_search_count=0, local_search_steps=99)
    plain = genetic(OBJECTIVE, SPACE, 2000, random.Random(5))
    assert genetic(OBJECTIVE, SPACE, 2000, random.Random(5), params=explicit) == plain
