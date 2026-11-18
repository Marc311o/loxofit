"""
Fast objective for the optimizers - the same number as `evaluate_plan(...).score`.

The reference implementation (evaluate.py) builds a whole Mesocycle of objects for
every candidate and recomputes everything that never changes: how an exercise
splits its sets between muscles, how long one of its sets takes, how many sets
the progression gives in week w. An optimizer scores tens of thousands of
candidates over the same exercises, so `Objective` computes those parts once:

- per exercise: volume weight per target muscle, time of one working set,
  rest between sets, ramp-up time, primary muscles (for warm-up decisions);
- per base sets: sets in every week of the mesocycle (progression + deload);
- per (exercise, base sets): volume and time in every week - cached on first use.

A candidate is then just exercise indices and base sets. Equivalence with the
reference implementation is checked by tests/engine/test_objective.py.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass

from app.engine.progression import deload_sets, progressed_sets
from app.engine.timing import rest_s, set_duration_s, warmup_duration_s, working_reps
from app.engine.types import EngineConfig, ExerciseSpec, MuscleTargets, PlannedExercise, Session

# One planned exercise: (index into Objective.exercises, base sets).
Gene = tuple[int, int]
# A base week: sessions in order, each an ordered list of genes.
Candidate = Sequence[Sequence[Gene]]


@dataclass(frozen=True, slots=True)
class _Exercise:
    weights: tuple[tuple[int, float], ...]  # (target muscle index, weight), weight > 0
    set_s: float  # one working set
    rest_s: float  # after one working set
    warmup_s: float  # ramp-up sets, when the exercise needs them
    is_compound: bool
    primary_mask: int  # primary muscles as a bitmask over all muscles


class Objective:
    """Scores base weeks of one optimization problem."""

    def __init__(
        self,
        exercises: Sequence[ExerciseSpec],
        targets: MuscleTargets,
        config: EngineConfig,
        weeks: int,
        session_limits: Sequence[int],
    ) -> None:
        if weeks < 2:
            raise ValueError(f"A mesocycle needs at least 2 weeks (training + deload), got {weeks}")
        self.exercises = tuple(exercises)
        self.config = config
        self.weeks = weeks
        self.training_weeks = weeks - 1
        self.session_limits = tuple(session_limits)

        # Only muscles with priority > 0 affect the score.
        scored = [(code, t) for code, t in targets.items() if t.priority > 0]
        index = {code: i for i, (code, _) in enumerate(scored)}
        self._mev = [t.mev for _, t in scored]
        self._tau = [(t.mav_upper - t.mev) / config.curve_k for _, t in scored]
        self._mrv = [t.mrv for _, t in scored]
        self._priority = [t.priority for _, t in scored]
        self._n_muscles = len(scored)

        all_muscles: dict[str, int] = {}
        for e in self.exercises:
            for muscle in e.muscle_roles:
                all_muscles.setdefault(muscle, len(all_muscles))

        self._specs = tuple(self._compile(e, index, all_muscles) for e in self.exercises)
        self._sets: dict[int, tuple[int, ...]] = {}
        self._cache: dict[
            Gene, tuple[tuple[tuple[int, tuple[float, ...]], ...], tuple[float, ...]]
        ] = {}

    def _compile(
        self, e: ExerciseSpec, index: dict[str, int], all_muscles: dict[str, int]
    ) -> _Exercise:
        config = self.config
        weights = tuple(
            (index[m], config.weight(role))
            for m, role in e.muscle_roles.items()
            if m in index and config.weight(role) > 0
        )
        mask = 0
        for m in e.primary_muscles():
            mask |= 1 << all_muscles[m]
        return _Exercise(
            weights=weights,
            set_s=set_duration_s(e, working_reps(e, config), config),
            rest_s=rest_s(e, config),
            warmup_s=warmup_duration_s(e, config),
            is_compound=e.is_compound,
            primary_mask=mask,
        )

    def sets_per_week(self, base: int) -> tuple[int, ...]:
        """Sets of an exercise with `base` sets in week 1, for every week incl. the deload."""
        sets = self._sets.get(base)
        if sets is None:
            if base < 1:
                raise ValueError(f"sets must be >= 1, got {base}")
            training = (progressed_sets(base, w, self.config) for w in range(1, self.weeks))
            sets = (*training, deload_sets(base, self.config))
            self._sets[base] = sets
        return sets

    def _gene(
        self, gene: Gene
    ) -> tuple[tuple[tuple[int, tuple[float, ...]], ...], tuple[float, ...]]:
        """Volume per target muscle per week and seconds per week (without ramp-up)."""
        cached = self._cache.get(gene)
        if cached is None:
            spec = self._specs[gene[0]]
            sets = self.sets_per_week(gene[1])
            volume = tuple((m, tuple(s * w for s in sets)) for m, w in spec.weights)
            rests = 0 if self.config.rest_before_next_exercise else 1
            seconds = tuple(s * spec.set_s + (s - rests) * spec.rest_s for s in sets)
            cached = (volume, seconds)
            self._cache[gene] = cached
        return cached

    def score(self, candidate: Candidate) -> float:
        """Volume score over the training weeks minus the time penalty over all weeks."""
        config = self.config
        weeks = self.weeks
        cap = config.session_volume_cap
        n = self._n_muscles
        total = [[0.0] * weeks for _ in range(n)]  # whole volume
        effective = [[0.0] * weeks for _ in range(n)]  # capped per session
        overtime = 0.0

        for s, session in enumerate(candidate):
            session_volume: dict[int, list[float]] = {}
            fixed = config.warmup_s + max(0, len(session) - 1) * config.transitions_s
            if config.rest_before_next_exercise and session:
                fixed -= self._specs[session[-1][0]].rest_s  # nothing follows the last set
            seconds = [fixed] * weeks
            trained = 0
            for gene in session:
                spec = self._specs[gene[0]]
                volume, gene_seconds = self._gene(gene)
                warm = (
                    spec.warmup_s if spec.is_compound and not (trained & spec.primary_mask) else 0.0
                )
                if spec.is_compound:
                    trained |= spec.primary_mask
                for w in range(weeks):
                    seconds[w] += gene_seconds[w] + warm
                for m, per_week in volume:
                    acc = session_volume.get(m)
                    if acc is None:
                        session_volume[m] = list(per_week)
                    else:
                        for w in range(weeks):
                            acc[w] += per_week[w]

            limit = self.session_limits[s]
            for w in range(weeks):
                over = seconds[w] / 60 - limit
                if over > 0:
                    overtime += over
            for m, per_week in session_volume.items():
                tot, eff = total[m], effective[m]
                for w in range(weeks):
                    v = per_week[w]
                    tot[w] += v
                    eff[w] += v if cap is None or v < cap else cap

        volume_score = 0.0
        lam = config.penalty_lambda
        for m in range(n):
            mev, tau, mrv, priority = self._mev[m], self._tau[m], self._mrv[m], self._priority[m]
            tot, eff = total[m], effective[m]
            for w in range(self.training_weeks):
                x = (eff[w] - mev) / tau
                u = 1.0 - math.exp(-x) if x >= 0 else x
                excess = tot[w] - mrv
                p = lam * excess * excess if excess > 0 else 0.0
                volume_score += priority * (u - p)

        return volume_score - config.time_penalty * overtime

    def to_sessions(self, candidate: Candidate) -> tuple[Session, ...]:
        """The candidate as engine objects - for the reference evaluation and for saving."""
        return tuple(
            Session(
                tuple(PlannedExercise(self.exercises[i], sets) for i, sets in session),
                self.session_limits[s],
            )
            for s, session in enumerate(candidate)
        )
