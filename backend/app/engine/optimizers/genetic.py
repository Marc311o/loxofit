"""
Genetic algorithm over base weeks.

Each generation: the `elitism` best candidates survive unchanged; every other
child gets two parents chosen by tournament selection, is crossed over with
probability `crossover_rate` and then mutated - one move from the search space
with probability `mutation_rate`, and another one with the same probability,
and so on (on average mutation_rate / (1 - mutation_rate) moves).

Crossover variants:
- "session": each session comes whole from one of the parents (uniform) -
  keeps sessions that work well together intact;
- "gene": within each session, every exercise either parent has goes to the
  child with probability 1/2 (sets from the parent that has it, or a random
  parent's if both do), then the session is repaired.

Memetic variant (local_search_count > 0): after each generation is built, its
`local_search_count` best candidates are refined by hill climbing - up to
`local_search_steps` random moves each, keeping a move if it is not worse. The
genetic algorithm explores, the local search polishes what it found. Those
evaluations come out of the same budget.
"""

import random
from dataclasses import dataclass
from typing import Literal

from app.engine.objective import Objective
from app.engine.optimizers.base import BudgetExhausted, Evaluator, ProgressCallback, SearchResult
from app.engine.space import Candidate, SearchSpace


@dataclass(frozen=True, slots=True)
class GeneticParams:
    population: int = 60
    tournament: int = 3
    crossover_rate: float = 0.9
    mutation_rate: float = 0.6
    elitism: int = 2
    crossover: Literal["session", "gene"] = "session"
    local_search_count: int = 0  # best candidates refined per generation; 0 - plain GA
    local_search_steps: int = 25  # moves tried per refined candidate

    def __post_init__(self) -> None:
        if self.population < 2:
            raise ValueError("population must be >= 2")
        if not 1 <= self.tournament <= self.population:
            raise ValueError("tournament must be between 1 and the population size")
        if not 0 <= self.elitism < self.population:
            raise ValueError("elitism must be below the population size")
        if not (0 <= self.crossover_rate <= 1 and 0 <= self.mutation_rate < 1):
            raise ValueError("rates must be probabilities (mutation_rate below 1)")
        if not 0 <= self.local_search_count <= self.population or self.local_search_steps < 0:
            raise ValueError("local search: count within the population, steps >= 0")


DEFAULT_PARAMS = GeneticParams()
MEMETIC_PARAMS = GeneticParams(local_search_count=2, local_search_steps=25)


def _tournament(scored: list[tuple[float, Candidate]], k: int, rng: random.Random) -> Candidate:
    return max(rng.sample(scored, k), key=lambda item: item[0])[1]


def _session_crossover(a: Candidate, b: Candidate, rng: random.Random) -> list[list]:
    return [list(rng.choice(pair)) for pair in zip(a, b, strict=True)]


def _gene_crossover(a: Candidate, b: Candidate, rng: random.Random) -> list[list]:
    child = []
    for sa, sb in zip(a, b, strict=True):
        da, db = dict(sa), dict(sb)
        genes = []
        for i in sorted(da.keys() | db.keys()):  # sorted - reproducible with the same seed
            if rng.random() < 0.5:
                genes.append((i, rng.choice([d[i] for d in (da, db) if i in d])))
        child.append(genes)
    return child


def _local_search(
    candidate: Candidate,
    score: float,
    steps: int,
    space: SearchSpace,
    evaluator: Evaluator,
    rng: random.Random,
) -> tuple[float, Candidate]:
    """Hill climbing from `candidate`: keep each move that is not worse."""
    for _ in range(steps):
        neighbour = space.mutate(candidate, rng)
        value = evaluator.score(neighbour)
        if value >= score:
            candidate, score = neighbour, value
    return score, candidate


def genetic(
    objective: Objective,
    space: SearchSpace,
    budget: int,
    rng: random.Random,
    on_progress: ProgressCallback | None = None,
    params: GeneticParams | None = None,
) -> SearchResult:
    params = params or DEFAULT_PARAMS
    evaluator = Evaluator(objective, budget, on_progress)
    crossover = _session_crossover if params.crossover == "session" else _gene_crossover
    try:
        scored = []
        for _ in range(params.population):
            candidate = space.random_candidate(rng)
            scored.append((evaluator.score(candidate), candidate))

        while True:
            scored.sort(key=lambda item: item[0], reverse=True)
            next_generation = scored[: params.elitism]
            while len(next_generation) < params.population:
                mother = _tournament(scored, params.tournament, rng)
                if rng.random() < params.crossover_rate:
                    father = _tournament(scored, params.tournament, rng)
                    child = space.repair(crossover(mother, father, rng))
                else:
                    child = mother
                while rng.random() < params.mutation_rate:
                    child = space.mutate(child, rng)
                next_generation.append((evaluator.score(child), child))
            if params.local_search_count:
                next_generation.sort(key=lambda item: item[0], reverse=True)
                for k in range(params.local_search_count):
                    score, candidate = next_generation[k]
                    next_generation[k] = _local_search(
                        candidate, score, params.local_search_steps, space, evaluator, rng
                    )
            scored = next_generation
    except BudgetExhausted:
        pass
    return evaluator.result()


def memetic(
    objective: Objective,
    space: SearchSpace,
    budget: int,
    rng: random.Random,
    on_progress: ProgressCallback | None = None,
    params: GeneticParams | None = None,
) -> SearchResult:
    """The genetic algorithm with local search - MEMETIC_PARAMS unless given others."""
    return genetic(objective, space, budget, rng, on_progress, params or MEMETIC_PARAMS)
