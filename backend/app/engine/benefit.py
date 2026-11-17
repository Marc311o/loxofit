"""Benefit of weekly volume for a muscle, with a penalty above MRV.

Above MEV: diminishing returns, u(V) = 1 - exp(-(V - MEV) / tau), tau = (MAV_upper - MEV) / k.
Below MEV: the tangent line at MEV, u(V) = (V - MEV) / tau - negative, growing linearly.
Above MRV: quadratic penalty lambda * (V - MRV)^2.

    score_m = priority_m * (u(E_m) - penalty(V_m))

V is the whole weekly volume. E is the effective volume - V without the sets
above the per-session cap (see volume.effective_volume); without a cap E = V.
"""

import math
from dataclasses import dataclass

from app.engine.types import EngineConfig, MuscleTarget, MuscleTargets
from app.engine.volume import Volume


def tau(target: MuscleTarget, curve_k: float) -> float:
    """Saturation scale: at V = MAV_upper the benefit reaches 1 - e^(-k)."""
    return (target.mav_upper - target.mev) / curve_k


def benefit(volume: float, target: MuscleTarget, curve_k: float) -> float:
    t = tau(target, curve_k)
    x = (volume - target.mev) / t
    if x >= 0:
        return 1.0 - math.exp(-x)
    return x


def mrv_penalty(volume: float, target: MuscleTarget, penalty_lambda: float) -> float:
    excess = max(0.0, volume - target.mrv)
    return penalty_lambda * excess**2


@dataclass(frozen=True, slots=True)
class MuscleScore:
    volume: float
    effective_volume: float
    benefit: float
    penalty: float
    score: float  # priority * (benefit - penalty)


def muscle_score(
    volume: float,
    target: MuscleTarget,
    config: EngineConfig,
    effective: float | None = None,
) -> MuscleScore:
    """Benefit from the effective volume, MRV penalty from the whole volume."""
    effective = volume if effective is None else effective
    u = benefit(effective, target, config.curve_k)
    p = mrv_penalty(volume, target, config.penalty_lambda)
    return MuscleScore(volume, effective, u, p, target.priority * (u - p))


def score_muscles(
    volume: Volume,
    targets: MuscleTargets,
    config: EngineConfig,
    effective: Volume | None = None,
) -> dict[str, MuscleScore]:
    """Breakdown per target muscle - for explanations and analysis.

    Muscles without volume count as V = 0; muscles without a target are ignored.
    Without `effective` the whole volume counts towards the benefit.
    """
    effective = volume if effective is None else effective
    return {
        muscle: muscle_score(volume.get(muscle, 0.0), target, config, effective.get(muscle, 0.0))
        for muscle, target in targets.items()
        if target.priority > 0
    }


def volume_score(
    volume: Volume,
    targets: MuscleTargets,
    config: EngineConfig,
    effective: Volume | None = None,
) -> float:
    """Sum of muscle scores for one week - the part of the objective the GA maximizes."""
    return sum(s.score for s in score_muscles(volume, targets, config, effective).values())
