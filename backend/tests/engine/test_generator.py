"""Plan generation in the engine: the search space it builds and the plan it returns."""

import pytest

from app.engine.focus import Focus
from app.engine.generator import (
    CandidateExercise,
    EmptySessionError,
    GenerationTask,
    build_search,
    generate,
)
from app.engine.types import MuscleTarget
from tests.engine.samples import BENCH, CLOSE_GRIP, CONFIG, CURL, FLY, ROW

EXERCISES = (
    CandidateExercise(BENCH, complexity=3, fatigue_cost=3, movement_pattern="horizontal_push"),
    CandidateExercise(ROW, complexity=3, fatigue_cost=3, movement_pattern="horizontal_pull"),
    CandidateExercise(FLY, complexity=1, fatigue_cost=1, movement_pattern="chest_fly"),
    CandidateExercise(CURL, complexity=1, fatigue_cost=1, movement_pattern="elbow_flexion"),
    CandidateExercise(CLOSE_GRIP, complexity=3, fatigue_cost=3, movement_pattern="horizontal_push"),
)
TARGETS = {m: MuscleTarget(4, 13, 16) for m in ("pec_major", "lats", "biceps", "triceps")}


def task(seed: int = 0, focuses=(Focus.PUSH, Focus.PULL)) -> GenerationTask:
    return GenerationTask(
        exercises=EXERCISES,
        focuses=focuses,
        session_minutes=(45,) * len(focuses),
        targets=TARGETS,
        config=CONFIG,
        weeks=4,
        seed=seed,
        budget=3000,
    )


def test_generated_plan_follows_the_focus_and_the_pattern_limit():
    result = generate(task())
    push, pull = result.sessions
    assert {i for i, _ in push} <= {0, 2, 4}  # bench, fly, close grip
    assert {i for i, _ in pull} <= {1, 3}  # row, curl
    assert not {0, 4} <= {i for i, _ in push}  # two horizontal pushes - never together
    assert result.evaluations == 3000
    assert result.history[-1][1] == result.score
    assert result.max_score == pytest.approx(4 * 3 * (1 - 2.718281828459045**-3))


def test_same_seed_same_plan():
    assert generate(task(seed=3)) == generate(task(seed=3))


def test_progress_is_reported():
    seen = []
    generate(task(), seen.append)
    assert seen and seen[-1].evaluations == 3000


def test_a_session_no_exercise_fits():
    with pytest.raises(EmptySessionError) as error:
        build_search(EXERCISES, (Focus.PUSH, Focus.LOWER), (60, 60), TARGETS, CONFIG, 4)
    assert error.value.session == 1
