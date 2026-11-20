"""
Baseline: build the plan step by step, always taking the single change that
raises the score the most - add an exercise with one set to a session, or one
more set to an exercise already in the plan. Stops when no change helps (a local
optimum) or the budget runs out. Deterministic: ties go to the first change found.
"""

import random

from app.engine.objective import Objective
from app.engine.optimizers.base import BudgetExhausted, Evaluator, ProgressCallback, SearchResult
from app.engine.space import Candidate, SearchSpace


def _neighbours(candidate: Candidate, space: SearchSpace) -> list[Candidate]:
    result = []
    for s, session in enumerate(candidate):
        for g, (i, sets) in enumerate(session):
            if sets < space.max_sets:
                genes = list(session)
                genes[g] = (i, sets + 1)
                result.append(candidate[:s] + (space.ordered(genes),) + candidate[s + 1 :])
        if len(session) < space.max_exercises:
            for i in space.pools[s]:
                if space.fits(s, session, i):
                    genes = [*session, (i, space.min_sets)]
                    result.append(candidate[:s] + (space.ordered(genes),) + candidate[s + 1 :])
    return result


def greedy(
    objective: Objective,
    space: SearchSpace,
    budget: int,
    rng: random.Random | None = None,  # unused - same signature as the other optimizers
    on_progress: ProgressCallback | None = None,
) -> SearchResult:
    evaluator = Evaluator(objective, budget, on_progress)
    current: Candidate = tuple(() for _ in range(space.sessions))  # start from nothing
    try:
        current_score = evaluator.score(current)
        while True:
            best, best_score = None, current_score
            for candidate in _neighbours(current, space):
                value = evaluator.score(candidate)
                if value > best_score:
                    best, best_score = candidate, value
            if best is None:
                break
            current, current_score = best, best_score
    except BudgetExhausted:
        pass
    # A session the greedy left empty gets its minimum, like any other result.
    # Scored outside the budget: it is the answer, not a step of the search.
    searched = evaluator.result()
    final = space.repair(current)
    return SearchResult(final, objective.score(final), searched.evaluations, searched.history)
