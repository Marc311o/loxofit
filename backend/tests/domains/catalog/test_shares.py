"""Unit tests of compute_muscle_shares - no database, objects built in memory."""

import pytest

from app.domains.catalog.enums import MuscleGroup, MuscleRole
from app.domains.catalog.models import ExerciseMuscleRole, Muscle
from app.domains.catalog.service import compute_muscle_shares

P, S, X = MuscleRole.PRIMARY, MuscleRole.SECONDARY, MuscleRole.STABILIZER
WEIGHTS = {P: 1.0, S: 0.5, X: 0.0}

_next_id = iter(range(1, 1000))


def role(name_en: str, r: MuscleRole) -> ExerciseMuscleRole:
    code = name_en.lower().replace(" ", "_")[:10]
    muscle = Muscle(
        id=next(_next_id),
        code=code,
        name_en=name_en,
        name_pl=name_en,
        muscle_group=MuscleGroup.CHEST,
        is_volume_target=True,
    )
    return ExerciseMuscleRole(muscle=muscle, role=r)


def shares(roles, weights=WEIGHTS) -> list[tuple[str, float]]:
    return [(s.muscle.name_en, s.share_pct) for s in compute_muscle_shares(roles, weights)]


def test_primary_and_two_secondaries():
    roles = [role("Triceps", S), role("Chest", P), role("Front delt", S)]
    # 1.0 / 2.0 = 50 %, 0.5 / 2.0 = 25 %; largest first, ties alphabetical
    assert shares(roles) == [("Chest", 50.0), ("Front delt", 25.0), ("Triceps", 25.0)]


def test_two_primaries_and_one_secondary():
    roles = [role("Hamstrings", S), role("Glutes", P), role("Erectors", P)]
    assert shares(roles) == [("Erectors", 40.0), ("Glutes", 40.0), ("Hamstrings", 20.0)]


def test_shares_are_rounded_to_one_decimal():
    roles = [role("A", P), role("B", P), role("C", P)]
    assert shares(roles) == [("A", 33.3), ("B", 33.3), ("C", 33.3)]  # sums to 99.9


def test_zero_weight_role_is_listed_with_zero_share():
    roles = [role("Chest", P), role("Core", X)]
    assert shares(roles) == [("Chest", 100.0), ("Core", 0.0)]


def test_role_missing_from_weights_counts_as_zero():
    roles = [role("Chest", P), role("Triceps", S)]
    assert shares(roles, {P: 1.0}) == [("Chest", 100.0), ("Triceps", 0.0)]


@pytest.mark.parametrize("roles", [[], [role("Core", X)]])
def test_no_division_by_zero(roles):
    assert all(pct == 0.0 for _, pct in shares(roles))
