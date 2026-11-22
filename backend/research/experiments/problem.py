"""
A scenario turned into what the optimizers take: the objective and the search space.

Built from the catalog spreadsheet and a config version from the registry - no
database, so every experiment can be repeated from the repository alone.
"""

from dataclasses import dataclass

from app.domains.model_config.versions import ConfigVersion
from app.engine.focus import Focus, template_focuses
from app.engine.generator import CandidateExercise, build_search
from app.engine.objective import Candidate, Objective
from app.engine.space import SearchSpace
from app.engine.types import MuscleTargets
from app.seeds.catalog_file import CatalogData
from research.engine_eval import build_config, build_specs, build_targets
from research.experiments.scenarios import Scenario


@dataclass(frozen=True)
class Problem:
    scenario: Scenario
    objective: Objective
    space: SearchSpace
    targets: MuscleTargets
    codes: tuple[str, ...]  # exercise code of every index in a candidate
    focuses: tuple[Focus, ...]

    def describe(self, candidate: Candidate) -> list[dict]:
        """A candidate as readable sessions - for the plans saved with the results."""
        return [
            {"focus": focus.value, "exercises": [[self.codes[i], sets] for i, sets in session]}
            for focus, session in zip(self.focuses, candidate, strict=True)
        ]


def available_exercises(catalog: CatalogData, equipment: frozenset[str] | None) -> list[str]:
    """Codes of the exercises the equipment allows: an exercise needs all its equipment."""
    if equipment is None:
        return [e.code for e in catalog.exercises]
    needs: dict[str, set[str]] = {e.code: set() for e in catalog.exercises}
    for row in catalog.exercise_equipment:
        needs[row.exercise].add(row.equipment)
    return [e.code for e in catalog.exercises if needs[e.code] <= equipment]


def build_problem(scenario: Scenario, catalog: CatalogData, version: ConfigVersion) -> Problem:
    specs = build_specs(catalog)
    rows = {e.code: e for e in catalog.exercises}
    codes = tuple(available_exercises(catalog, scenario.equipment))
    exercises = [
        CandidateExercise(
            spec=specs[c],
            complexity=rows[c].complexity,
            fatigue_cost=rows[c].fatigue_cost,
            movement_pattern=rows[c].movement_pattern.value,
        )
        for c in codes
    ]
    focuses = template_focuses(scenario.template, scenario.sessions)
    targets = build_targets(version, catalog)
    objective, space = build_search(
        exercises,
        focuses,
        [scenario.minutes] * scenario.sessions,
        targets,
        build_config(version),
        scenario.weeks,
    )
    return Problem(scenario, objective, space, targets, codes, focuses)
