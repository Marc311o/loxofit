import math

import pytest

from app.engine.benefit import benefit, mrv_penalty, muscle_score, tau, volume_score
from app.engine.types import EngineConfig, MuscleTarget
from tests.engine.samples import CONFIG

PEC = MuscleTarget(mev=5, mav_upper=16, mrv=20)
K = 3.0


def test_tau():
    assert tau(PEC, K) == pytest.approx(11 / 3)


@pytest.mark.parametrize(
    ("volume", "expected"),
    [
        (5, 0.0),  # at MEV no benefit yet
        (8, 0.558),  # 1 - e^(-3/3.667)
        (12, 0.852),  # 1 - e^(-7/3.667)
        (16, 0.950),  # at MAV_upper: 1 - e^(-k)
    ],
)
def test_benefit_above_mev(volume, expected):
    assert benefit(volume, PEC, K) == pytest.approx(expected, abs=1e-3)


def test_benefit_reaches_one_minus_e_to_minus_k_at_mav_upper():
    assert benefit(PEC.mav_upper, PEC, K) == pytest.approx(1 - math.exp(-K))


def test_diminishing_returns():
    # The first sets above MEV are worth more than the last ones before MAV.
    first = benefit(8, PEC, K) - benefit(5, PEC, K)
    last = benefit(16, PEC, K) - benefit(13, PEC, K)
    assert first > 4 * last


def test_benefit_below_mev_is_linear_and_negative():
    # (2 - 5) / 3.667 = -0.818; every set below MEV costs the same 1/tau.
    assert benefit(2, PEC, K) == pytest.approx(-0.818, abs=1e-3)
    assert benefit(0, PEC, K) - benefit(1, PEC, K) == pytest.approx(-1 / tau(PEC, K))


def test_benefit_is_continuous_and_smooth_at_mev():
    eps = 1e-6
    below, at, above = (benefit(PEC.mev + d, PEC, K) for d in (-eps, 0, eps))
    assert below == pytest.approx(at, abs=1e-5) == pytest.approx(above, abs=1e-5)
    # Same slope on both sides (1 / tau).
    slope_below = (at - below) / eps
    slope_above = (above - at) / eps
    assert slope_below == pytest.approx(slope_above, rel=1e-3)


@pytest.mark.parametrize(("volume", "expected"), [(15, 0.0), (20, 0.0), (22, 0.2), (24, 0.8)])
def test_mrv_penalty_is_zero_up_to_mrv_then_quadratic(volume, expected):
    # lambda = 0.05: 2 sets over -> 0.05 * 4 = 0.2; 4 sets over -> 0.05 * 16 = 0.8
    assert mrv_penalty(volume, PEC, 0.05) == pytest.approx(expected)


def test_going_over_mrv_lowers_the_score():
    # Benefit gained beyond MRV is tiny, the penalty quickly outweighs it.
    at_mrv = muscle_score(20, PEC, CONFIG).score
    over = muscle_score(24, PEC, CONFIG).score
    assert over < at_mrv


def test_priority_scales_the_score():
    doubled = MuscleTarget(mev=5, mav_upper=16, mrv=20, priority=2.0)
    assert muscle_score(12, doubled, CONFIG).score == pytest.approx(
        2 * muscle_score(12, PEC, CONFIG).score
    )


def test_volume_score_sums_target_muscles():
    targets = {"pec_major": PEC, "biceps": PEC}
    # biceps missing from volume -> V = 0 -> benefit -5 / 3.667
    expected = benefit(12, PEC, K) + benefit(0, PEC, K)
    assert volume_score({"pec_major": 12.0}, targets, CONFIG) == pytest.approx(expected)


def test_volume_score_ignores_untargeted_and_zero_priority_muscles():
    targets = {"pec_major": PEC, "erectors": MuscleTarget(1, 2, 3, priority=0)}
    volume = {"pec_major": 12.0, "triceps": 6.0, "erectors": 0.0}
    assert volume_score(volume, targets, CONFIG) == pytest.approx(benefit(12, PEC, K))


def test_curve_k_comes_from_config():
    steeper = EngineConfig(role_weights=CONFIG.role_weights, curve_k=4.0)
    assert muscle_score(12, PEC, steeper).benefit > muscle_score(12, PEC, CONFIG).benefit
