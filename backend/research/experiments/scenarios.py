"""
Experiment scenarios: what the user fixes - split, number and length of sessions,
equipment. The generator chooses the exercises and their sets.

The scenarios are split in two. Optimizer parameters are tuned on the TUNE set and
the algorithms are compared on the TEST set, so no algorithm is judged on the
problems its parameters were picked for.
"""

from dataclasses import dataclass
from enum import StrEnum

from app.engine.focus import Template


class Split(StrEnum):
    TUNE = "tune"
    TEST = "test"


# A home gym: dumbbells, benches, a pull-up bar and a ball - plus bodyweight exercises.
HOME = frozenset({"dumbbells", "flat_bench", "adj_bench", "pullup_bar", "swiss_ball"})


@dataclass(frozen=True)
class Scenario:
    name: str
    template: Template
    sessions: int
    minutes: int  # limit of every session
    split: Split
    equipment: frozenset[str] | None = None  # None - a full gym
    weeks: int = 5  # mesocycle: 4 training weeks + deload


SCENARIOS: tuple[Scenario, ...] = (
    # tuning
    Scenario("fbw-3x60-gym", Template.FULL_BODY, 3, 60, Split.TUNE),
    Scenario("fbw-2x60-gym", Template.FULL_BODY, 2, 60, Split.TUNE),
    Scenario("ul-4x45-gym", Template.UPPER_LOWER, 4, 45, Split.TUNE),
    Scenario("ppl-3x60-home", Template.PUSH_PULL_LEGS, 3, 60, Split.TUNE, HOME),
    # comparison
    Scenario("ul-4x60-gym", Template.UPPER_LOWER, 4, 60, Split.TEST),
    Scenario("ppl-3x45-gym", Template.PUSH_PULL_LEGS, 3, 45, Split.TEST),
    Scenario("ppl-6x60-gym", Template.PUSH_PULL_LEGS, 6, 60, Split.TEST),
    Scenario("fbw-3x45-home", Template.FULL_BODY, 3, 45, Split.TEST, HOME),
)

BY_NAME = {s.name: s for s in SCENARIOS}


def scenarios(split: Split | None = None) -> tuple[Scenario, ...]:
    return tuple(s for s in SCENARIOS if split is None or s.split == split)
