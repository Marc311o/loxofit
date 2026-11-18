"""Baseline: score random candidates, keep the best."""

import random

from app.engine.objective import Objective
from app.engine.optimizers.base import BudgetExhausted, Evaluator, ProgressCallback, SearchResult
from app.engine.space import SearchSpace


def random_search(
    objective: Objective,
    space: SearchSpace,
    budget: int,
    rng: random.Random,
    on_progress: ProgressCallback | None = None,
) -> SearchResult:
    evaluator = Evaluator(objective, budget, on_progress)
    try:
        while True:
            evaluator.score(space.random_candidate(rng))
    except BudgetExhausted:
        pass
    return evaluator.result()
