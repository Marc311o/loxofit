"""Statistics helpers of the analysis (skipped where the research packages are missing)."""

import pytest

pytest.importorskip("pandas")
pytest.importorskip("scipy")
pytest.importorskip("matplotlib")

from research.experiments.analysis import a12, holm, polish_number  # noqa: E402


def test_holm_multiplies_by_the_remaining_tests_and_stays_monotone():
    # sorted: 0.01 * 3, 0.02 * 2 = 0.04, 0.04 * 1 -> raised to the previous 0.04
    assert holm([0.04, 0.01, 0.02]) == pytest.approx([0.04, 0.03, 0.04])
    assert holm([0.5, 0.6]) == [1.0, 1.0]  # capped at 1


def test_a12_is_the_probability_of_winning():
    assert a12([3, 4], [1, 2]) == 1.0
    assert a12([1, 2], [3, 4]) == 0.0
    assert a12([1, 2], [1, 2]) == 0.5


def test_polish_numbers():
    assert [polish_number(x) for x in (-1.5, 0.3, 5000, 30000)] == ["−1,5", "0,3", "5000", "30 000"]
