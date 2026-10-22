"""Effective volume: sets x role weight, summed per muscle."""

import pytest

from app.engine.types import EngineConfig, PlannedExercise, Session
from app.engine.volume import exercise_volume, weekly_volume
from tests.engine.samples import BENCH, CONFIG, CURL, FLY, PLANK_LIKE, ROW, P, S


def session(*items: tuple, max_minutes: int = 90) -> Session:
    return Session(tuple(PlannedExercise(ex, sets) for ex, sets in items), max_minutes)


def test_single_exercise_splits_sets_by_role():
    # 3 sets of bench: chest primary (1.0), front delt and triceps secondary (0.5)
    assert exercise_volume(PlannedExercise(BENCH, 3), CONFIG) == {
        "pec_major": 3.0,
        "delt_ant": 1.5,
        "triceps": 1.5,
    }


def test_role_without_weight_contributes_nothing():
    # Stabilizer has no weight in CONFIG -> erectors are not in the result at all.
    assert exercise_volume(PlannedExercise(PLANK_LIKE, 2), CONFIG) == {"rect_abd": 2.0}


def test_volume_of_one_session():
    # Worked example: bench 3 + row 3
    assert weekly_volume([session((BENCH, 3), (ROW, 3))], CONFIG) == {
        "pec_major": 3.0,
        "delt_ant": 1.5,
        "triceps": 1.5,
        "lats": 3.0,
        "trapezius": 3.0,
        "delt_post": 1.5,
        "biceps": 1.5,
    }


def test_same_muscle_from_several_exercises_and_sessions_is_summed():
    upper_a = session((BENCH, 3), (CURL, 2))  # biceps: 0 + 2.0
    upper_b = session((ROW, 4), (FLY, 2))  # biceps: 4 x 0.5 = 2.0
    volume = weekly_volume([upper_a, upper_b], CONFIG)

    assert volume["pec_major"] == pytest.approx(3.0 + 2.0)  # bench + fly
    assert volume["delt_ant"] == pytest.approx(1.5 + 1.0)  # 3 x 0.5 + 2 x 0.5
    assert volume["biceps"] == pytest.approx(2.0 + 2.0)  # curl + row


def test_weights_come_from_config():
    # Counting secondary sets fully instead of as half sets.
    full_sets = EngineConfig(role_weights={P: 1.0, S: 1.0})
    assert weekly_volume([session((BENCH, 3))], full_sets)["triceps"] == 3.0


def test_empty_week_has_no_volume():
    assert weekly_volume([], CONFIG) == {}
