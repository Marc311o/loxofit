"""
Reads data from spreadsheet. Loads muscles, exercises, equipment and relations in 2 phases:
1. Validates data (catalog_file.load_catalog)
2. If no errors found - seeds database
"""

import asyncio
import logging
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base, SessionLocal, engine
from app.domains.catalog.models import (
    Equipment,
    Exercise,
    ExerciseEquipment,
    ExerciseMuscleRole,
    ExerciseSubstitute,
    Muscle,
)
from app.scripts.catalog_file import DATA_FILE, CatalogData, SeedDataError, SeedRow, load_catalog

logger = logging.getLogger("seed")


# SAVE DATA


async def _upsert(
    db: AsyncSession, model: type[Base], rows: list[SeedRow], key: str = "code"
) -> dict[str, int]:
    """Upserts data"""

    if not rows:
        return {}
    values = [r.model_dump() for r in rows]
    key_column = getattr(model, key)

    stmt = insert(model).values(values)
    stmt = stmt.on_conflict_do_update(
        index_elements=[key_column],
        set_={column: stmt.excluded[column] for column in values[0] if column != key},
    ).returning(key_column, model.id)

    result = await db.execute(stmt)
    return {k: id_ for k, id_ in result.all()}


async def write_catalog(db: AsyncSession, data: CatalogData) -> None:
    """Phase 2: saving data"""

    # Parents
    muscle_ids = await _upsert(db, Muscle, data.muscles)
    equipment_ids = await _upsert(db, Equipment, data.equipment)
    exercise_ids = await _upsert(db, Exercise, data.exercises)

    # Relations
    seeded = list(exercise_ids.values())
    for link in (ExerciseMuscleRole, ExerciseEquipment, ExerciseSubstitute):
        await db.execute(delete(link).where(link.exercise_id.in_(seeded)))

    role_values = [
        {"exercise_id": exercise_ids[r.exercise], "muscle_id": muscle_ids[r.muscle], "role": r.role}
        for r in data.roles
    ]
    equipment_values = [
        {"exercise_id": exercise_ids[r.exercise], "equipment_id": equipment_ids[r.equipment]}
        for r in data.exercise_equipment
    ]
    substitute_values = [
        {
            "exercise_id": exercise_ids[r.exercise],
            "substitute_exercise_id": exercise_ids[r.substitute],
            "priority_score": r.priority_score,
        }
        for r in data.substitutes
    ]
    for link, values in (
        (ExerciseMuscleRole, role_values),
        (ExerciseEquipment, equipment_values),
        (ExerciseSubstitute, substitute_values),
    ):
        if values:
            await db.execute(insert(link).values(values))

    logger.info(
        "Catalog: %d muscles, %d equipments, %d exercises, "
        "%d roles, %d exercise-equipment relations, %d substitutes",
        len(muscle_ids),
        len(equipment_ids),
        len(exercise_ids),
        len(role_values),
        len(equipment_values),
        len(substitute_values),
    )

    # Exercises from outside the sheet remain
    result = await db.execute(
        select(Exercise.code).where(Exercise.code.not_in(exercise_ids.keys()))
    )
    if orphans := result.scalars().all():
        logger.warning("Exercises unchanged: %s", ", ".join(orphans))


async def seed_catalog(db: AsyncSession, path: Path = DATA_FILE) -> None:
    data = load_catalog(path)
    await write_catalog(db, data)
    await db.commit()


async def main() -> int:
    try:
        async with SessionLocal() as db:
            await seed_catalog(db)
    except SeedDataError as exc:
        logger.error(
            "Catalog file is corrupted - %d errors found. Nothing has changed:", len(exc.errors)
        )
        for error in exc.errors:
            logger.error("  %s", error)
        return 1
    finally:
        await engine.dispose()
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    raise SystemExit(asyncio.run(main()))
