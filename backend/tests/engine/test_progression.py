"""
Mesocycle progression with the default config: +15 % sets per week (max 5 per
exercise), RIR 3 -> 1, deload at 50 % of week-1 sets with RIR 4.
"""

import pytest

from app.engine.progression import (
    build_mesocycle,
    deload_sets,
    progressed_sets,
    rir_for_week,
    round_half_up,
)
from app.engine.types import PlannedExercise, Session
from app.engine.volume import weekly_volume
from tests.engine.samples import BENCH, CONFIG, FLY, ROW


def test_round_half_up_differs_from_builtin_round():
    assert round(2.5) == 2
    assert [round_half_up(x) for x in (2.5, 3.5, 2.49, 0.5)] == [3, 4, 2, 1]


@pytest.mark.parametrize(
    ("base", "expected"),
    [
        (3, [3, 3, 4, 5]),
        (2, [2, 2, 3, 3]),  # 2.00, 2.30, 2.65, 3.04
        (4, [4, 5, 5, 5]),  # 4.60 -> 5 then capped
        (5, [5, 5, 5, 5]),  # the cap
    ],
)
def test_progressed_sets(base, expected):
    assert [progressed_sets(base, w, CONFIG) for w in range(1, 5)] == expected


def test_progression_never_goes_below_week_one():
    # Base above the cap
    assert progressed_sets(6, 3, CONFIG) == 6


@pytest.mark.parametrize(("base", "expected"), [(1, 1), (2, 1), (3, 2), (4, 2), (5, 3)])
def test_deload_sets(base, expected):
    # 50 % rounded half up, at least 1
    assert deload_sets(base, CONFIG) == expected


@pytest.mark.parametrize(
    ("training_weeks", "expected"),
    [
        (1, [3]),
        (3, [3, 2, 1]),
        (4, [3, 2, 2, 1]),  # 3, 2.33, 1.67, 1
        (5, [3, 3, 2, 2, 1]),  # 3, 2.5, 2, 1.5, 1
    ],
)
def test_rir_goes_linearly_from_start_to_end(training_weeks, expected):
    rirs = [rir_for_week(w, training_weeks, CONFIG) for w in range(1, training_weeks + 1)]
    assert rirs == expected


@pytest.fixture
def base_week() -> tuple[Session, ...]:
    upper = Session((PlannedExercise(BENCH, 3), PlannedExercise(FLY, 2)), max_minutes=60)
    pull = Session((PlannedExercise(ROW, 4),), max_minutes=45)
    return (upper, pull)


def test_mesocycle_structure(base_week):
    meso = build_mesocycle(base_week, weeks=5, config=CONFIG)

    assert len(meso.weeks) == 5
    assert [w.is_deload for w in meso.weeks] == [False] * 4 + [True]
    assert len(meso.training_weeks) == 4
    assert [w.rir for w in meso.weeks] == [3, 2, 2, 1, 4]


def test_first_week_equals_base_and_layout_is_kept(base_week):
    meso = build_mesocycle(base_week, weeks=5, config=CONFIG)

    assert meso.weeks[0].sessions == base_week
    for week in meso.weeks:
        assert [s.max_minutes for s in week.sessions] == [60, 45]
        assert [[p.exercise.code for p in s.exercises] for s in week.sessions] == [
            ["bb_bench", "pec_deck_fly"],
            ["cable_row_seated"],
        ]


def test_sets_per_week(base_week):
    meso = build_mesocycle(base_week, weeks=5, config=CONFIG)
    bench_sets = [w.sessions[0].exercises[0].sets for w in meso.weeks]
    row_sets = [w.sessions[1].exercises[0].sets for w in meso.weeks]

    assert bench_sets == [3, 3, 4, 5, 2]  # last deload
    assert row_sets == [4, 5, 5, 5, 2]


def test_muscle_volume_grows_then_drops_in_deload(base_week):
    meso = build_mesocycle(base_week, weeks=5, config=CONFIG)
    chest = [weekly_volume(w.sessions, CONFIG)["pec_major"] for w in meso.weeks]

    training, deload = chest[:-1], chest[-1]
    assert training == sorted(training)  # non-decreasing
    assert deload < training[0]


def test_mesocycle_needs_at_least_two_weeks(base_week):
    with pytest.raises(ValueError):
        build_mesocycle(base_week, weeks=1, config=CONFIG)
