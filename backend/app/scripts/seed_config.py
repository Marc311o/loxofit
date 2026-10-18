"""
Configurations are IMMUTABLE and VERSIONED. Do not remove old configs, as resetting db will erase them

Adding new version:
1. Add ConfigVersion at the end of CONFIGS variable (DO NOT REMOVE OTHERS),
2. If default – change DEFAULT_CONFIG_NAME,
3. Launch script
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionLocal, engine
from app.domains.catalog.enums import MuscleRole
from app.domains.model_config.enums import VolumeMode
from app.domains.model_config.models import ConfigRoleWeight, ModelConfig

logger = logging.getLogger("seed")


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
_MANAGED_COLUMNS = {"id", "name", "is_default", "created_at"}


def check_registry() -> None:

    names = [c.name for c in CONFIGS]
    if len(names) != len(set(names)):
        raise ValueError(f"Duplicate config names: {names}")
    if DEFAULT_CONFIG_NAME not in names:
        raise ValueError(f"No DEFAULT_CONFIG_NAME={DEFAULT_CONFIG_NAME!r} in CONFIGS")

    allowed = {c.name for c in ModelConfig.__table__.columns} - _MANAGED_COLUMNS
    for version in CONFIGS:
        if unknown := set(version.params) - allowed:
            raise ValueError(f"{version.name}: unknown parameters {sorted(unknown)}")
        if missing := set(MuscleRole) - set(version.role_weights):
            raise ValueError(f"{version.name}: no weights set for roles {sorted(missing)}")


async def upsert_version(db: AsyncSession, version: ConfigVersion) -> int:
    """Creates version if such does not exist. Does not change existing ones. Returns id."""
    stmt = insert(ModelConfig).values(name=version.name, **version.params)
    stmt = stmt.on_conflict_do_update(
        index_elements=[ModelConfig.name], set_={"name": stmt.excluded.name}
    ).returning(ModelConfig.id)
    config_id = (await db.execute(stmt)).scalar_one()

    weights = insert(ConfigRoleWeight).values(
        [{"config_id": config_id, "role": r, "weight": w} for r, w in version.role_weights.items()]
    )
    await db.execute(weights.on_conflict_do_nothing(index_elements=["config_id", "role"]))
    return config_id


async def config_drift(db: AsyncSession, config_id: int, version: ConfigVersion) -> list[str]:
    """Catches differences between configs in base and configs in code"""
    config = (await db.execute(select(ModelConfig).where(ModelConfig.id == config_id))).scalar_one()
    result = await db.execute(
        select(ConfigRoleWeight.role, ConfigRoleWeight.weight).where(
            ConfigRoleWeight.config_id == config_id
        )
    )
    saved_weights = dict(result.all())

    diffs = [
        f"{name}: base {getattr(config, name)!r}, code {value!r}"
        for name, value in version.params.items()
        if getattr(config, name) != value
    ]
    diffs += [
        f"weight '{role}': base {saved_weights.get(role)!r}, code {weight!r}"
        for role, weight in version.role_weights.items()
        if saved_weights.get(role) != weight
    ]
    return diffs


async def set_default(db: AsyncSession, name: str) -> None:
    await db.execute(
        update(ModelConfig)
        .where(ModelConfig.is_default, ModelConfig.name != name)
        .values(is_default=False)
    )
    await db.execute(update(ModelConfig).where(ModelConfig.name == name).values(is_default=True))


async def seed_configs(db: AsyncSession) -> None:
    check_registry()

    for version in CONFIGS:
        config_id = await upsert_version(db, version)
        if drift := await config_drift(db, config_id, version):
            logger.warning(
                "%s: Base definition differ from code. Versions are immutable. "
                "Add new config with different name",
                version.name,
            )
            for line in drift:
                logger.warning("  %s", line)

    await set_default(db, DEFAULT_CONFIG_NAME)

    known = [c.name for c in CONFIGS]
    result = await db.execute(select(ModelConfig.name).where(ModelConfig.name.not_in(known)))
    if orphans := result.scalars().all():
        logger.warning(
            "Base includes configs not listed in CONFIGS: %s",
            ", ".join(orphans),
        )

    await db.commit()
    logger.info("Config: %s; default: %s", ", ".join(known), DEFAULT_CONFIG_NAME)


async def main() -> None:
    try:
        async with SessionLocal() as db:
            await seed_configs(db)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    asyncio.run(main())
