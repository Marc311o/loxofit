"""
Registry of model configurations - no database access.

Configurations are IMMUTABLE and VERSIONED. Do not remove old configs,
as resetting db will erase them.

Adding new version:
1. Add ConfigVersion at the end of CONFIGS (DO NOT REMOVE OTHERS),
2. If default - change DEFAULT_CONFIG_NAME,
3. Launch seed_config.

Shared by seed_config.py (writes them to the database) and engine_eval.py (runs the engine
with them without a database).
"""

from dataclasses import dataclass, field
from typing import Any

from app.domains.catalog.enums import MuscleRole
from app.domains.model_config.enums import VolumeMode

Landmarks = tuple[float, float, float]


@dataclass(frozen=True)
class ConfigVersion:
    name: str
    params: dict[str, Any] = field(default_factory=dict)
    role_weights: dict[MuscleRole, float] = field(default_factory=dict)
    landmarks: dict[str, Landmarks] = field(default_factory=dict)


FRACTIONAL_SETS = {
    MuscleRole.PRIMARY: 1.0,
    MuscleRole.SECONDARY: 0.5,
    MuscleRole.STABILIZER: 0.0,
}

RP_2017_LANDMARKS: dict[str, Landmarks] = {
    "pec_major": (10, 20, 22),  # chest
    "lats": (10, 22, 25),  # back
    "trapezius": (0, 20, 26),
    "delt_ant": (0, 8, 12),  # front delts - trained by every press
    "delt_mid": (8, 22, 26),  # side / rear delts
    "delt_post": (8, 22, 26),
    "biceps": (8, 20, 26),
    "triceps": (6, 14, 18),
    "quads": (8, 18, 20),
    "bic_fem": (6, 16, 20),  # hamstrings
    "glute_max": (0, 12, 16),
    "rect_abd": (0, 20, 25),  # abs
}

CONFIGS: list[ConfigVersion] = [
    ConfigVersion(
        name="global-v1",
        params={
            "volume_mode": VolumeMode.GLOBAL,
            "global_mev": 4.0,
            "global_mav_upper": 13.0,
            "global_mrv": 16.0,
            "session_volume_cap": None,
        },
        role_weights=FRACTIONAL_SETS,
    ),
    ConfigVersion(
        name="per-muscle-v1",
        params={
            "volume_mode": VolumeMode.PER_MUSCLE,
            "session_volume_cap": 11.0,  # Remmert et al. 2025
        },
        role_weights=FRACTIONAL_SETS,
        landmarks=RP_2017_LANDMARKS,
    ),
    ConfigVersion(
        name="per-muscle-v2",
        params={
            "volume_mode": VolumeMode.PER_MUSCLE,
            "session_volume_cap": 11.0,  # Remmert et al. 2025
            "rest_before_next_exercise": True,
            "transitions_s": 60,
        },
        role_weights=FRACTIONAL_SETS,
        landmarks=RP_2017_LANDMARKS,
    ),
]

DEFAULT_CONFIG_NAME = "per-muscle-v2"


def get_config(name: str) -> ConfigVersion:
    for version in CONFIGS:
        if version.name == name:
            return version
    known = ", ".join(c.name for c in CONFIGS)
    raise KeyError(f"Unknown config {name!r}. Known: {known}")
