"""Session focus: which exercises may go into which session."""

from app.engine.focus import Focus, Template, fits, session_pools, template_focuses
from app.engine.types import ExerciseSpec
from tests.engine.samples import BENCH, CLOSE_GRIP, CURL, LEG_EXT_UNI, PLANK_LIKE, ROW, P, S

SQUAT = ExerciseSpec("bb_squat", True, {"quads": P, "glute_max": P, "erectors": S})
DEADLIFT = ExerciseSpec("bb_deadlift", True, {"erectors": P, "glute_max": P, "lats": S})
CALF = ExerciseSpec("calf_raise", False, {"gastrocnemius": P})  # a muscle no focus knows


def test_templates_repeat_their_cycle():
    assert template_focuses(Template.UPPER_LOWER, 4) == (
        Focus.UPPER,
        Focus.LOWER,
        Focus.UPPER,
        Focus.LOWER,
    )
    assert template_focuses(Template.PUSH_PULL_LEGS, 4) == (
        Focus.PUSH,
        Focus.PULL,
        Focus.LOWER,
        Focus.PUSH,
    )
    assert template_focuses(Template.FULL_BODY, 2) == (Focus.FULL_BODY, Focus.FULL_BODY)


def test_primary_muscles_decide_secondary_do_not():
    assert fits(BENCH, Focus.PUSH)  # triceps and front delt are only secondary
    assert fits(ROW, Focus.PULL)  # biceps secondary, lats + traps primary
    assert not fits(ROW, Focus.PUSH)
    assert fits(DEADLIFT, Focus.LOWER)  # lats only secondary
    assert not fits(DEADLIFT, Focus.PULL)


def test_an_exercise_must_fit_with_all_its_primary_muscles():
    # Close-grip bench: chest + triceps primary - push yes, upper yes, lower no.
    assert fits(CLOSE_GRIP, Focus.PUSH) and fits(CLOSE_GRIP, Focus.UPPER)
    assert not fits(CLOSE_GRIP, Focus.LOWER)


def test_core_fits_everywhere_and_full_body_takes_anything():
    assert all(fits(PLANK_LIKE, focus) for focus in Focus)
    assert fits(CALF, Focus.FULL_BODY)
    assert not fits(CALF, Focus.LOWER)  # unknown muscles only in full body sessions


def test_session_pools():
    exercises = [BENCH, ROW, CURL, SQUAT, LEG_EXT_UNI, PLANK_LIKE]
    pools = session_pools(exercises, (Focus.UPPER, Focus.LOWER, Focus.FULL_BODY))
    assert pools == ((0, 1, 2, 5), (3, 4, 5), (0, 1, 2, 3, 4, 5))
