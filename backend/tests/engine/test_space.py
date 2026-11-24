"""Search space: random candidates, repair and moves always stay valid."""

import random

import pytest

from app.engine.space import SearchSpace, recommended_rank
from tests.engine.samples import BENCH, CLOSE_GRIP, CURL, FLY, PLANK_LIKE, ROW, SHOULDER_PRESS

EXERCISES = (BENCH, ROW, FLY, CURL, PLANK_LIKE, SHOULDER_PRESS, CLOSE_GRIP)
# Session 0: push-ish, session 1: everything; rank = compound first, as the domain would order.
SPACE = SearchSpace(
    exercises=EXERCISES,
    pools=((0, 2, 4, 5, 6), (0, 1, 2, 3, 4, 5, 6)),
    rank=(0, 1, 4, 5, 6, 2, 3),
    max_sets=5,
    max_exercises=4,
)


def test_random_candidates_are_valid():
    rng = random.Random(0)
    for _ in range(200):
        assert SPACE.is_valid(SPACE.random_candidate(rng))


@pytest.mark.parametrize("seed", range(20))
def test_every_move_keeps_the_candidate_valid(seed):
    rng = random.Random(seed)
    candidate = SPACE.random_candidate(rng)
    for _ in range(200):
        candidate = SPACE.mutate(candidate, rng)
        assert SPACE.is_valid(candidate)


def test_moves_explore_the_whole_space():
    # From one candidate, enough moves reach every allowed exercise in every session.
    rng = random.Random(1)
    candidate = SPACE.random_candidate(rng)
    seen = [set(), set()]
    for _ in range(2000):
        candidate = SPACE.mutate(candidate, rng)
        for s, session in enumerate(candidate):
            seen[s] |= {i for i, _ in session}
    assert seen == [set(SPACE.pools[0]), set(SPACE.pools[1])]


def test_repair_fixes_anything():
    broken = [
        [(1, 9), (0, 0), (0, 3)],  # row not allowed in session 0, sets out of bounds, duplicate
        [],  # empty session
    ]
    assert SPACE.repair(broken) == (((0, 2),), ((0, 2),))  # at least min_sets = 2


def test_sessions_follow_the_rank():
    # Fly (rank 4) after bench press (0) and close-grip bench (3), whatever the input order.
    assert SPACE.ordered([(2, 3), (6, 2), (0, 3)]) == ((0, 3), (6, 2), (2, 3))


def test_swap_prefers_exercises_for_the_same_muscle():
    # Bench -> mostly fly or close-grip (both train the chest), rarely something else.
    rng = random.Random(2)
    space = SearchSpace(EXERCISES, ((0, 1, 2, 3, 6),), rank=tuple(range(7)), similar_share=0.8)
    bench_only = (((0, 3),),)
    picks = [space._swap(bench_only, rng)[0][0][0] for _ in range(1000)]
    chest = sum(p in (2, 6) for p in picks) / len(picks)
    assert chest == pytest.approx(0.9, abs=0.04)  # 80% similar + half of the 20% random picks


def test_generator_never_proposes_a_single_set():
    rng = random.Random(3)
    candidate = SPACE.random_candidate(rng)
    for _ in range(500):
        candidate = SPACE.mutate(candidate, rng)
        assert all(sets >= 2 for session in candidate for _, sets in session)


# Movement patterns of EXERCISES: bench and close-grip bench are both horizontal pushes.
PATTERNS = ("h_push", "h_pull", "fly", "elbow_flexion", "core", "v_push", "h_push")
ONE_PER_PATTERN = SearchSpace(
    exercises=EXERCISES,
    pools=SPACE.pools,
    rank=SPACE.rank,
    max_exercises=4,
    patterns=PATTERNS,
    max_per_pattern=1,
)


def test_one_exercise_per_movement_pattern():
    rng = random.Random(4)
    candidate = ONE_PER_PATTERN.random_candidate(rng)
    for _ in range(1000):
        candidate = ONE_PER_PATTERN.mutate(candidate, rng)
        assert ONE_PER_PATTERN.is_valid(candidate)
        for session in candidate:
            patterns = [PATTERNS[i] for i, _ in session]
            assert len(patterns) == len(set(patterns))


def test_repair_keeps_the_first_exercise_of_a_pattern():
    # Bench and close-grip bench in one session: the second horizontal push goes.
    assert ONE_PER_PATTERN.repair([[(0, 3), (6, 3), (2, 2)], [(1, 3)]]) == (
        ((0, 3), (2, 2)),
        ((1, 3),),
    )


def test_a_pattern_limit_needs_patterns():
    with pytest.raises(ValueError):
        SearchSpace(EXERCISES, SPACE.pools, SPACE.rank, max_per_pattern=1)


def test_a_session_without_allowed_exercises_is_rejected():
    with pytest.raises(ValueError):
        SearchSpace(EXERCISES, ((0,), ()), rank=tuple(range(7)))


def test_recommended_rank_puts_compounds_first_then_harder_then_more_fatiguing():
    # BENCH, ROW, FLY, CURL, PLANK_LIKE, SHOULDER_PRESS, CLOSE_GRIP
    complexity = [3, 3, 1, 1, 2, 3, 3]
    fatigue = [3, 4, 1, 1, 1, 2, 3]
    rank = recommended_rank(EXERCISES, complexity, fatigue)
    order = sorted(range(len(EXERCISES)), key=lambda i: rank[i])
    # compounds by fatigue (row, bench, close grip - catalog order on a tie, press);
    # then isolation by complexity (plank-like), ties in catalog order (fly, curl)
    assert [EXERCISES[i].code for i in order] == [
        ROW.code, BENCH.code, CLOSE_GRIP.code, SHOULDER_PRESS.code,
        PLANK_LIKE.code, FLY.code, CURL.code,
    ]  # fmt: skip
