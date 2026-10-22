"""Objective of a whole mesocycle."""

import pytest

from app.engine.benefit import volume_score
from app.engine.evaluate import evaluate, evaluate_plan
from app.engine.progression import build_mesocycle
from app.engine.types import EngineConfig, MuscleTarget, PlannedExercise, Session
from app.engine.volume import weekly_volume
from tests.engine.samples import BENCH, CONFIG, FLY, ROW

PEC = MuscleTarget(mev=5, mav_upper=16, mrv=20)
LATS = MuscleTarget(mev=5, mav_upper=16, mrv=20)  # same landmarks -> easy to compare
TARGETS = {"pec_major": PEC, "lats": LATS}


def week(*items: tuple, max_minutes: int = 120) -> tuple[Session, ...]:
    return (Session(tuple(PlannedExercise(ex, sets) for ex, sets in items), max_minutes),)


def test_volume_score_is_summed_over_training_weeks_only():
    base = week((BENCH, 3), (ROW, 3))
    meso = build_mesocycle(base, weeks=3, config=CONFIG)  # 2 training weeks + deload
    result = evaluate(meso, TARGETS, CONFIG)

    expected = sum(
        volume_score(weekly_volume(w.sessions, CONFIG), TARGETS, CONFIG)
        for w in meso.training_weeks
    )
    assert result.volume_score == pytest.approx(expected)
    deload = result.weeks[-1]
    assert deload.muscles == {} and deload.volume_score == 0.0
    assert deload.volume  # volume is reported but not scored


def test_score_is_volume_score_minus_time_penalty():
    result = evaluate_plan(week((BENCH, 3), (ROW, 3), max_minutes=10), 3, TARGETS, CONFIG)
    assert result.time_penalty > 0
    assert result.score == pytest.approx(result.volume_score - result.time_penalty)


def test_time_penalty_counts_every_session_including_deload():
    result = evaluate_plan(week((BENCH, 3), max_minutes=10), 3, TARGETS, CONFIG)
    overtime = sum(w.overtime_minutes for w in result.weeks)
    assert result.weeks[-1].overtime_minutes > 0  # even the short deload is over 10 min
    assert result.time_penalty == pytest.approx(CONFIG.time_penalty * overtime)


def test_no_penalty_within_time_limit():
    result = evaluate_plan(week((BENCH, 3), (ROW, 3)), 3, TARGETS, CONFIG)
    assert result.time_penalty == 0.0
    assert result.score == result.volume_score


def test_spreading_sets_beats_piling_them_on_one_muscle():
    # Same 6 sets per week: all on chest vs. split between chest and back.
    # Diminishing returns + negative score below MEV favor the split.
    piled = evaluate_plan(week((BENCH, 6)), 3, TARGETS, CONFIG)
    split = evaluate_plan(week((BENCH, 3), (ROW, 3)), 3, TARGETS, CONFIG)
    assert split.score > piled.score


def test_more_useful_volume_increases_the_score():
    low = evaluate_plan(week((BENCH, 2), (ROW, 2)), 3, TARGETS, CONFIG)
    high = evaluate_plan(week((BENCH, 3), (FLY, 2), (ROW, 4)), 3, TARGETS, CONFIG)
    assert high.score > low.score


def test_progression_past_mrv_is_penalized_in_later_weeks():
    # Base week is under MRV; +15 % per week pushes it over, and the objective sees it.
    tight = {"pec_major": MuscleTarget(mev=5, mav_upper=12, mrv=14)}
    base = week((BENCH, 4), (FLY, 4), (BENCH, 4))  # week 1: 12 sets, week 2: 5+5+5 = 15
    result = evaluate_plan(base, 3, tight, CONFIG)

    week1, week2 = (w.muscles["pec_major"] for w in result.weeks[:2])
    assert week1.volume == 12 and week1.penalty == 0
    assert week2.volume == 15 and week2.penalty == pytest.approx(0.05 * 1**2)


def test_breakdown_reports_session_minutes():
    result = evaluate_plan(week((BENCH, 3), (FLY, 2)), 2, TARGETS, CONFIG)
    # Week 1 = base week: 1192 s from the timing worked example.
    assert result.weeks[0].session_minutes == pytest.approx((1192 / 60,))


def test_time_penalty_weight_comes_from_config():
    strict = EngineConfig(role_weights=CONFIG.role_weights, time_penalty=1.0)
    base = week((BENCH, 3), max_minutes=10)
    assert evaluate_plan(base, 3, TARGETS, strict).time_penalty == pytest.approx(
        10 * evaluate_plan(base, 3, TARGETS, CONFIG).time_penalty
    )
