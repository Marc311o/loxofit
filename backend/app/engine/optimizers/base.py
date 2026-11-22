"""
What every optimizer shares: a budget of objective evaluations, the best
candidate found so far and its history, progress reports.

The budget is counted in evaluations, not seconds, so results do not depend on
the machine and every optimizer gets exactly the same amount of work.
"""

from collections.abc import Callable
from dataclasses import dataclass

from app.engine.objective import Objective
from app.engine.space import Candidate


@dataclass(frozen=True, slots=True)
class Progress:
    evaluations: int
    budget: int
    best_score: float


ProgressCallback = Callable[[Progress], None]


@dataclass(frozen=True, slots=True)
class SearchResult:
    best: Candidate
    score: float
    evaluations: int  # used; may be below the budget (greedy stops on its own)
    history: tuple[tuple[int, float], ...]  # (evaluations, best score) at each improvement


class BudgetExhausted(Exception):
    """Raised by Evaluator.score when the budget is used up - ends the search."""


class Evaluator:
    """Scores candidates within a budget and remembers the best one."""

    def __init__(
        self,
        objective: Objective,
        budget: int,
        on_progress: ProgressCallback | None = None,
        report_every: int = 500,
    ) -> None:
        if budget < 1:
            raise ValueError(f"budget must be >= 1, got {budget}")
        self.objective = objective
        self.budget = budget
        self.used = 0
        self.best: Candidate | None = None
        self.best_score = float("-inf")
        self.history: list[tuple[int, float]] = []
        self._on_progress = on_progress
        self._report_every = report_every

    @property
    def remaining(self) -> int:
        return self.budget - self.used

    def score(self, candidate: Candidate) -> float:
        if self.used >= self.budget:
            raise BudgetExhausted
        self.used += 1
        value = self.objective.score(candidate)
        if value > self.best_score:
            self.best, self.best_score = candidate, value
            self.history.append((self.used, value))
        if self._on_progress and self.used % self._report_every == 0:
            self._on_progress(Progress(self.used, self.budget, self.best_score))
        return value

    def result(self) -> SearchResult:
        """The best candidate; also sends the last progress report if one is due."""
        if self.best is None:
            raise RuntimeError("nothing was evaluated")
        if self._on_progress and self.used % self._report_every != 0:
            self._on_progress(Progress(self.used, self.budget, self.best_score))
        return SearchResult(self.best, self.best_score, self.used, tuple(self.history))
