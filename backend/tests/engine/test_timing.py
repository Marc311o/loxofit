"""Session duration. Worked example (default config):

bench, compound, tempo 3010 -> 4 s/rep x 8 reps = 32 s per set
    3 working sets           3 x 32           =  96
    rests between them       2 x 150          = 300
    warm-up 8+5+3 reps       16 x 4 + 3 x 60  = 244   -> 640 s
pec deck, isolation, default tempo 2010 -> 3 s/rep x 12 reps = 36 s per set
    2 working sets + 1 rest  2 x 36 + 90      = 162 s (no warm-up: isolation)
session = 300 general warm-up + 640 + 90 transition + 162 = 1192 s = 19.87 min
"""

import pytest

from app.engine.timing import (
    overtime_minutes,
    rep_duration_s,
    session_duration_s,
    set_duration_s,
    total_overtime_minutes,
)
from app.engine.types import PlannedExercise, Session
from tests.engine.samples import (
    BENCH,
    CLOSE_GRIP,
    CONFIG,
    FLY,
    LEG_EXT_UNI,
    ROW,
    SHOULDER_PRESS,
)


def session(*items: tuple, max_minutes: int = 60) -> Session:
    return Session(tuple(PlannedExercise(ex, sets) for ex, sets in items), max_minutes)


@pytest.mark.parametrize(
    ("tempo", "seconds"),
    [
        ("3010", 4.0),
        ("2010", 3.0),
        ("30X0", 4.0),  # X in a movement phase = explosive_phase_s (1 s)
        ("3110", 5.0),
        ("0000", 2.0),  # movements still take 1 s each, pauses take 0
        ("x0x0", 2.0),  # lower case accepted
    ],
)
def test_rep_duration(tempo, seconds):
    assert rep_duration_s(tempo, 1.0) == seconds


@pytest.mark.parametrize("tempo", ["301", "30100", "3a10", "3X10", "301X"])
def test_invalid_tempo_is_rejected(tempo):
    with pytest.raises(ValueError):
        rep_duration_s(tempo, 1.0)


def test_unilateral_set_takes_twice_as_long():
    # 2010 -> 3 s/rep x 12 reps x 2 sides
    assert set_duration_s(LEG_EXT_UNI, 12, CONFIG) == 72.0


def test_worked_example_session():
    s = session((BENCH, 3), (FLY, 2))
    assert session_duration_s(s, CONFIG) == pytest.approx(1192)


def test_single_exercise_has_no_transition():
    # 300 + bench 640
    assert session_duration_s(session((BENCH, 3)), CONFIG) == pytest.approx(940)


def test_no_warmup_when_primary_muscle_already_trained():
    # Close-grip bench after bench: pec_major already primary -> no ramp-up sets.
    # Close-grip, default tempo 2010 -> 3 s x 8 reps = 24 s: 3 x 24 + 2 x 150 = 372
    with_bench = session_duration_s(session((BENCH, 3), (CLOSE_GRIP, 3)), CONFIG)
    assert with_bench == pytest.approx(300 + 640 + 90 + 372)


def test_warmup_when_primary_muscles_are_new():
    # Shoulder press after bench: delt_ant was only secondary there -> warm-up.
    # Default tempo 2010 -> 3 s/rep. Warm-up: 16 reps x 3 + 3 x 60 = 228.
    # Shoulder press: 3 x (8 x 3) + 2 x 150 + 228 = 600
    total = session_duration_s(session((BENCH, 3), (SHOULDER_PRESS, 3)), CONFIG)
    assert total == pytest.approx(300 + 640 + 90 + 600)


def test_order_matters_for_warmups():
    # Row first and bench second both get warm-ups (no shared primary muscles).
    a = session_duration_s(session((BENCH, 3), (ROW, 3)), CONFIG)
    b = session_duration_s(session((ROW, 3), (BENCH, 3)), CONFIG)
    assert a == pytest.approx(b)


def test_overtime_minutes():
    s = session((BENCH, 3), (FLY, 2), max_minutes=15)  # 19.87 min
    assert overtime_minutes(s, CONFIG) == pytest.approx(1192 / 60 - 15)
    assert overtime_minutes(session((BENCH, 3), max_minutes=60), CONFIG) == 0.0


def test_total_overtime_sums_sessions():
    over = session((BENCH, 3), (FLY, 2), max_minutes=15)
    ok = session((BENCH, 3), max_minutes=60)
    assert total_overtime_minutes([over, ok, over], CONFIG) == pytest.approx(2 * (1192 / 60 - 15))
