"""
Baseline: hill climbing with random restarts. From a random candidate, apply one
random move (the same moves the genetic algorithm mutates with) and keep the
result if it is not worse - equal scores are accepted to cross plateaus. After
`patience` moves without improvement the climb restarts from a new random candidate.
"""

import random

from app.engine.objective import Objective
from app.engine.optimizers.base import BudgetExhausted, Evaluator, ProgressCallback, SearchResult
from app.engine.space import SearchSpace


def hill_climbing(
    objective: Objective,
    space: SearchSpace,
    budget: int,
    rng: random.Random,
    on_progress: ProgressCallback | None = None,
    patience: int = 500,
) -> SearchResult:
    evaluator = Evaluator(objective, budget, on_progress)
    try:
        while True:
            current = space.random_candidate(rng)
            current_score = evaluator.score(current)
            stale = 0
            while stale < patience:
                neighbour = space.mutate(current, rng)
                value = evaluator.score(neighbour)
                stale = 0 if value > current_score else stale + 1
                if value >= current_score:
                    current, current_score = neighbour, value
    except BudgetExhausted:
        pass
    return evaluator.result()
