"""
Search space shared by all optimizers: what a candidate may contain and the
small changes ("moves") that turn one candidate into a neighbouring one.

A candidate is a tuple of sessions, each a tuple of genes (exercise index, base
sets) - the format `Objective.score` takes. Candidates are immutable, so a move
returns a new candidate and copies only the session it changed.

Exercise order inside a session is not searched. Every session is kept sorted
by `rank` (compound first, then technically harder and more fatiguing - computed
by the caller from the catalog), the same order the plan editor recommends.
That keeps the search space smaller and the result readable.

At least `min_sets` (2) sets per exercise: a single set is rarely worth the setup
and the warm-up of a new exercise, and a plan of one-set exercises is hard to
follow. It limits only what the generator proposes - the user may still set 1 set.
"""

import random
from collections.abc import Sequence
from dataclasses import dataclass, field

from app.engine.objective import Gene
from app.engine.types import ExerciseSpec

Session = tuple[Gene, ...]
Candidate = tuple[Session, ...]

# How often each move is tried; a move that does not apply falls back to another.
MOVE_WEIGHTS: dict[str, float] = {
    "sets": 0.35,  # one exercise +-1 set
    "swap": 0.30,  # replace an exercise, usually by a similar one
    "add": 0.15,
    "remove": 0.10,
    "move": 0.10,  # an exercise to another session
}


@dataclass(frozen=True)
class SearchSpace:
    exercises: tuple[ExerciseSpec, ...]
    pools: tuple[tuple[int, ...], ...]  # exercises allowed in each session
    rank: tuple[int, ...]  # position of each exercise in the session order
    min_sets: int = 2
    max_sets: int = 5
    max_exercises: int = 8  # per session
    similar_share: float = 0.8  # how often "swap" picks an exercise sharing a primary muscle
    _similar: tuple[frozenset[int], ...] = field(init=False, repr=False)
    _allowed: tuple[frozenset[int], ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if len(self.rank) != len(self.exercises):
            raise ValueError("rank needs one entry per exercise")
        if any(len(pool) == 0 for pool in self.pools):
            raise ValueError("every session needs at least one allowed exercise")
        primaries = [e.primary_muscles() for e in self.exercises]
        similar = tuple(
            frozenset(j for j, other in enumerate(primaries) if j != i and p & other)
            for i, p in enumerate(primaries)
        )
        object.__setattr__(self, "_similar", similar)
        object.__setattr__(self, "_allowed", tuple(frozenset(pool) for pool in self.pools))

    @property
    def sessions(self) -> int:
        return len(self.pools)

    # -- building and fixing candidates -----------------------------------------------

    def ordered(self, session: Sequence[Gene]) -> Session:
        return tuple(sorted(session, key=lambda gene: self.rank[gene[0]]))

    def random_candidate(self, rng: random.Random) -> Candidate:
        """Every session: a random number of distinct allowed exercises with random sets."""
        result = []
        for pool in self.pools:
            k = rng.randint(1, min(self.max_exercises, len(pool)))
            genes = [(i, rng.randint(self.min_sets, self.max_sets)) for i in rng.sample(pool, k)]
            result.append(self.ordered(genes))
        return tuple(result)

    def repair(self, candidate: Sequence[Sequence[Gene]]) -> Candidate:
        """Make any candidate valid: allowed and distinct exercises, sets and size in bounds."""
        result = []
        for s, session in enumerate(candidate):
            seen: set[int] = set()
            genes = []
            for i, sets in session:
                if i in self._allowed[s] and i not in seen:
                    seen.add(i)
                    genes.append((i, min(self.max_sets, max(self.min_sets, sets))))
            genes = genes[: self.max_exercises]
            if not genes:  # a session with nothing to do: put its best-ranked exercise back
                first = min(self.pools[s], key=lambda i: self.rank[i])
                genes = [(first, self.min_sets)]
            result.append(self.ordered(genes))
        return tuple(result)

    def is_valid(self, candidate: Candidate) -> bool:
        return len(candidate) == self.sessions and candidate == self.repair(candidate)

    # -- moves ------------------------------------------------------------------------

    def mutate(self, candidate: Candidate, rng: random.Random) -> Candidate:
        """One random move. Tries the moves in a random weighted order until one applies."""
        names = list(MOVE_WEIGHTS)
        weights = [MOVE_WEIGHTS[n] for n in names]
        while names:
            name = rng.choices(names, weights)[0]
            result = getattr(self, f"_{name}")(candidate, rng)
            if result is not None:
                return result
            k = names.index(name)
            del names[k], weights[k]
        return candidate

    def _replace(self, candidate: Candidate, s: int, session: Sequence[Gene]) -> Candidate:
        return candidate[:s] + (self.ordered(session),) + candidate[s + 1 :]

    def _sets(self, candidate: Candidate, rng: random.Random) -> Candidate | None:
        s = rng.randrange(self.sessions)
        session = list(candidate[s])
        g = rng.randrange(len(session))
        i, sets = session[g]
        options = [v for v in (sets - 1, sets + 1) if self.min_sets <= v <= self.max_sets]
        if not options:
            return None
        session[g] = (i, rng.choice(options))
        return self._replace(candidate, s, session)

    def _swap(self, candidate: Candidate, rng: random.Random) -> Candidate | None:
        s = rng.randrange(self.sessions)
        session = list(candidate[s])
        g = rng.randrange(len(session))
        i, sets = session[g]
        used = {e for e, _ in session}
        free = [j for j in self.pools[s] if j not in used]
        similar = [j for j in free if j in self._similar[i]]
        options = similar if similar and rng.random() < self.similar_share else free
        if not options:
            return None
        session[g] = (rng.choice(options), sets)
        return self._replace(candidate, s, session)

    def _add(self, candidate: Candidate, rng: random.Random) -> Candidate | None:
        s = rng.randrange(self.sessions)
        session = list(candidate[s])
        used = {e for e, _ in session}
        free = [j for j in self.pools[s] if j not in used]
        if len(session) >= self.max_exercises or not free:
            return None
        session.append((rng.choice(free), rng.randint(self.min_sets, self.max_sets)))
        return self._replace(candidate, s, session)

    def _remove(self, candidate: Candidate, rng: random.Random) -> Candidate | None:
        s = rng.randrange(self.sessions)
        session = list(candidate[s])
        if len(session) <= 1:
            return None
        del session[rng.randrange(len(session))]
        return self._replace(candidate, s, session)

    def _move(self, candidate: Candidate, rng: random.Random) -> Candidate | None:
        if self.sessions < 2:
            return None
        a, b = rng.sample(range(self.sessions), 2)
        source, target = list(candidate[a]), list(candidate[b])
        if len(source) <= 1 or len(target) >= self.max_exercises:
            return None
        g = rng.randrange(len(source))
        i, sets = source[g]
        if i not in self._allowed[b] or any(e == i for e, _ in target):
            return None
        del source[g]
        target.append((i, sets))
        return self._replace(self._replace(candidate, a, source), b, target)
