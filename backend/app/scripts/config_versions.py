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


@dataclass(frozen=True)
class ConfigVersion:
    name: str
    params: dict[str, Any] = field(default_factory=dict)
    role_weights: dict[MuscleRole, float] = field(default_factory=dict)


FRACTIONAL_SETS = {
    MuscleRole.PRIMARY: 1.0,
    MuscleRole.SECONDARY: 0.5,
    MuscleRole.STABILIZER: 0.0,
}

CONFIGS: list[ConfigVersion] = [
    ConfigVersion(
        name="global-v1",
        params={
            "volume_mode": VolumeMode.GLOBAL,
            "global_mev": 4.0,
            "global_mav_upper": 13.0,
            "global_mrv": 16.0,
        },
        role_weights=FRACTIONAL_SETS,
    ),
]

DEFAULT_CONFIG_NAME = "global-v1"


def get_config(name: str) -> ConfigVersion:
    for version in CONFIGS:
        if version.name == name:
            return version
    known = ", ".join(c.name for c in CONFIGS)
    raise KeyError(f"Unknown config {name!r}. Known: {known}")
