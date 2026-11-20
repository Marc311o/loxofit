"""
Reference evaluate_plan vs. the fast Objective on the same random candidates.
Synthetic but realistic problem (fixed seed, no database): 45 exercises,
14 target muscles, 4 sessions x 6 exercises, 5-week mesocycle.
"""

import random
import time

from app.engine.evaluate import evaluate_plan
from app.engine.objective import Objective
from app.engine.types import EngineConfig, ExerciseSpec, MuscleTarget, Role

MUSCLES = [
    "pec_major", "delt_ant", "delt_mid", "delt_post", "triceps", "biceps", "lats",
    "trapezius", "quads", "bic_fem", "glute_max", "rect_abd", "ext_obl", "int_obl",
]  # fmt: skip
WEEKS = 5
LIMITS = [60, 60, 60, 60]
CANDIDATES = 3000


def main() -> None:
    rng = random.Random(1)
    exercises = []
    for i in range(45):
        muscles = rng.sample(MUSCLES, rng.randint(1, 4))
        roles = {m: rng.choice([Role.PRIMARY, Role.SECONDARY, Role.STABILIZER]) for m in muscles}
        roles[muscles[0]] = Role.PRIMARY
        exercises.append(
            ExerciseSpec(f"e{i}", rng.random() < 0.7, roles, tempo=rng.choice([None, "3010"]))
        )
    targets = {m: MuscleTarget(4, 13, 16) for m in MUSCLES}
    config = EngineConfig(role_weights={Role.PRIMARY: 1.0, Role.SECONDARY: 0.5})
    objective = Objective(exercises, targets, config, WEEKS, LIMITS)
    candidates = [
        [[(i, rng.randint(1, 5)) for i in rng.sample(range(45), 6)] for _ in LIMITS]
        for _ in range(CANDIDATES)
    ]

    start = time.perf_counter()
    for c in candidates:
        evaluate_plan(objective.to_sessions(c), WEEKS, targets, config)
    reference = (time.perf_counter() - start) / CANDIDATES

    start = time.perf_counter()
    for c in candidates:
        objective.score(c)
    fast = (time.perf_counter() - start) / CANDIDATES

    print(f"reference: {reference * 1e3:.3f} ms per candidate")
    print(f"fast:      {fast * 1e6:.0f} us per candidate ({reference / fast:.0f}x faster)")


if __name__ == "__main__":
    main()
