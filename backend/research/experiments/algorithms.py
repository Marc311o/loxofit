"""
The algorithms the experiments run: the comparison set and the tuning grid.

Each entry is an algorithm family (random, greedy, hill, ga, memetic) with one set
of parameters - a variant. Variants are looked up by key in the worker processes,
so only the key travels between processes.
"""

import random
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from functools import partial
from itertools import product
from typing import Any

from app.engine.objective import Objective
from app.engine.optimizers import (
    GeneticParams,
    SearchResult,
    genetic,
    greedy,
    hill_climbing,
    random_search,
)
from app.engine.optimizers.genetic import DEFAULT_PARAMS, MEMETIC_PARAMS
from app.engine.space import SearchSpace

Optimizer = Callable[[Objective, SearchSpace, int, random.Random], SearchResult]


@dataclass(frozen=True)
class Algorithm:
    family: str
    variant: str
    run: Optimizer = field(repr=False)
    params: dict[str, Any] = field(default_factory=dict)

    @property
    def key(self) -> str:
        return f"{self.family}:{self.variant}"


def _genetic(params: GeneticParams, family: str, variant: str) -> Algorithm:
    run = partial(genetic, params=params)
    return Algorithm(family, variant, run, params=_params(params))


def _params(params: GeneticParams) -> dict[str, Any]:
    return {k: getattr(params, k) for k in params.__dataclass_fields__}


def _hill(patience: int, variant: str) -> Algorithm:
    run = partial(hill_climbing, patience=patience)
    return Algorithm("hill", variant, run, params={"patience": patience})


# -- comparison: one variant per family, picked by the tuning suite ------------------------
# The lowest mean rank over the TUNE scenarios (analysis.best_variants). The memetic grid
# was run on the default GA, and its winner is the default local search (2 x 25 steps).

COMPARISON: tuple[Algorithm, ...] = (
    Algorithm("random", "default", random_search),
    Algorithm("greedy", "default", greedy),
    _hill(1000, "tuned"),
    _genetic(replace(DEFAULT_PARAMS, population=120), "ga", "tuned"),
    _genetic(MEMETIC_PARAMS, "memetic", "tuned"),
)

# -- tuning grid ----------------------------------------------------------------------


def _tuning_grid() -> tuple[Algorithm, ...]:
    grid: list[Algorithm] = [_hill(p, f"patience={p}") for p in (200, 500, 1000, 2000)]
    ga_grid = product((30, 60, 120), (0.3, 0.6, 0.9), ("session", "gene"))
    for population, mutation, crossover in ga_grid:
        params = GeneticParams(population=population, mutation_rate=mutation, crossover=crossover)
        grid.append(_genetic(params, "ga", f"pop={population} mut={mutation} cx={crossover}"))
    for count, steps in product((1, 2, 5), (10, 25, 50)):
        params = GeneticParams(local_search_count=count, local_search_steps=steps)
        grid.append(_genetic(params, "memetic", f"ls={count}x{steps}"))
    return tuple(grid)


TUNING: tuple[Algorithm, ...] = _tuning_grid()

SUITES: dict[str, tuple[Algorithm, ...]] = {"compare": COMPARISON, "tune": TUNING}
REGISTRY: dict[str, Algorithm] = {a.key: a for suite in SUITES.values() for a in suite}
