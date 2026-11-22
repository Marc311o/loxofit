"""
Session focus - which exercises the generator may put into a session.

An exercise fits a session when all its primary muscles belong to the session's
focus. Secondary muscles may fall outside it (a row still works the biceps on
a back day). Core muscles fit every focus. Templates are presets of focuses
for common splits; "custom" lets the user set each session's focus.
"""

from collections.abc import Sequence
from enum import StrEnum

from app.engine.types import ExerciseSpec


class Focus(StrEnum):
    FULL_BODY = "full_body"
    UPPER = "upper"
    LOWER = "lower"
    PUSH = "push"
    PULL = "pull"


class Template(StrEnum):
    FULL_BODY = "full_body"
    UPPER_LOWER = "upper_lower"
    PUSH_PULL_LEGS = "push_pull_legs"


CORE = frozenset({"rect_abd", "ext_obl", "int_obl"})

PUSH_MUSCLES = frozenset({"pec_major", "delt_ant", "delt_mid", "triceps"})
PULL_MUSCLES = frozenset({"lats", "trapezius", "delt_post", "biceps"})
LOWER_MUSCLES = frozenset({"quads", "bic_fem", "glute_max", "erectors", "calf"})

# Primary muscles allowed in a session of each focus; None - any muscle.
FOCUS_MUSCLES: dict[Focus, frozenset[str] | None] = {
    Focus.FULL_BODY: None,
    Focus.UPPER: PUSH_MUSCLES | PULL_MUSCLES | CORE,
    Focus.LOWER: LOWER_MUSCLES | CORE,
    Focus.PUSH: PUSH_MUSCLES | CORE,
    Focus.PULL: PULL_MUSCLES | CORE,
}

TEMPLATE_CYCLE: dict[Template, tuple[Focus, ...]] = {
    Template.FULL_BODY: (Focus.FULL_BODY,),
    Template.UPPER_LOWER: (Focus.UPPER, Focus.LOWER),
    Template.PUSH_PULL_LEGS: (Focus.PUSH, Focus.PULL, Focus.LOWER),
}


def template_focuses(template: Template, sessions: int) -> tuple[Focus, ...]:
    """Focus of every session: the template's cycle repeated, e.g. U, L, U, L."""
    cycle = TEMPLATE_CYCLE[template]
    return tuple(cycle[i % len(cycle)] for i in range(sessions))


def fits(exercise: ExerciseSpec, focus: Focus) -> bool:
    allowed = FOCUS_MUSCLES[focus]
    return allowed is None or exercise.primary_muscles() <= allowed


def session_pools(
    exercises: Sequence[ExerciseSpec], focuses: Sequence[Focus]
) -> tuple[tuple[int, ...], ...]:
    """Indices of the exercises that fit each session."""
    return tuple(tuple(i for i, e in enumerate(exercises) if fits(e, focus)) for focus in focuses)
