from dataclasses import dataclass

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.catalog.enums import EquipmentCategory, MovementPattern, MuscleGroup, MuscleRole
from app.domains.catalog.models import Equipment, Exercise, ExerciseMuscleRole, Muscle
from app.domains.model_config.models import ConfigRoleWeight, ModelConfig

P, S = MuscleRole.PRIMARY, MuscleRole.SECONDARY


@dataclass
class Catalog:
    muscles: dict[str, Muscle]
    equipment: dict[str, Equipment]
    exercises: dict[str, Exercise]


def _muscle(code: str, name_en: str, name_pl: str, group: MuscleGroup) -> Muscle:
    return Muscle(code=code, name_en=name_en, name_pl=name_pl, muscle_group=group)


def _exercise(code, name_en, name_pl, group, pattern, roles, equipment, compound=True):
    return Exercise(
        code=code,
        name_en=name_en,
        name_pl=name_pl,
        main_group=group,
        movement_pattern=pattern,
        is_compound=compound,
        fatigue_cost=2,
        complexity=2,
        muscle_roles=[ExerciseMuscleRole(muscle=m, role=r) for m, r in roles],
        equipment=equipment,
    )


@pytest.fixture
async def catalog(db: AsyncSession) -> Catalog:
    m = {
        "pec_major": _muscle(
            "pec_major", "Pectoralis major", "Piersiowy większy", MuscleGroup.CHEST
        ),
        "delt_ant": _muscle(
            "delt_ant", "Anterior deltoid", "Naramienny przedni", MuscleGroup.SHOULDERS
        ),
        "triceps": _muscle("triceps", "Triceps brachii", "Trójgłowy ramienia", MuscleGroup.ARMS),
        "biceps": _muscle("biceps", "Biceps brachii", "Dwugłowy ramienia", MuscleGroup.ARMS),
        "lats": _muscle("lats", "Latissimus dorsi", "Najszerszy grzbietu", MuscleGroup.BACK),
    }
    eq = {
        "barbell": Equipment(
            code="barbell",
            name_en="Barbell",
            name_pl="Sztanga",
            category=EquipmentCategory.FREE_WEIGHTS,
        ),
        "flat_bench": Equipment(
            code="flat_bench",
            name_en="Flat bench",
            name_pl="Ławka płaska",
            category=EquipmentCategory.STATION,
        ),
        "cable_station": Equipment(
            code="cable_station",
            name_en="Cable station",
            name_pl="Wyciąg",
            category=EquipmentCategory.CABLE,
        ),
        "lat_pulldown": Equipment(
            code="lat_pulldown",
            name_en="Lat pull-down machine",
            name_pl="Wyciąg górny",
            category=EquipmentCategory.CABLE,
        ),
    }
    ex = {
        "bb_bench": _exercise(
            "bb_bench",
            "Barbell bench press",
            "Wyciskanie sztangi leżąc",
            MuscleGroup.CHEST,
            MovementPattern.HORIZONTAL_PUSH,
            [(m["pec_major"], P), (m["delt_ant"], S), (m["triceps"], S)],
            [eq["barbell"], eq["flat_bench"]],
        ),
        "cable_fly": _exercise(
            "cable_fly",
            "Cable fly",
            "Rozpiętki na wyciągu",
            MuscleGroup.CHEST,
            MovementPattern.CHEST_FLY,
            [(m["pec_major"], P), (m["delt_ant"], S)],
            [eq["cable_station"]],
            compound=False,
        ),
        "lat_pulldown": _exercise(
            "lat_pulldown",
            "Lat pull-down",
            "Ściąganie drążka",
            MuscleGroup.BACK,
            MovementPattern.VERTICAL_PULL,
            [(m["lats"], P), (m["biceps"], S)],
            [eq["lat_pulldown"]],
        ),
        "cable_curl": _exercise(
            "cable_curl",
            "Cable curl",
            "Uginanie ramion na wyciągu",
            MuscleGroup.ARMS,
            MovementPattern.ELBOW_FLEXION,
            [(m["biceps"], P)],
            [eq["cable_station"]],
            compound=False,
        ),
    }
    db.add_all([*m.values(), *eq.values(), *ex.values()])
    await db.flush()  # assigns ids
    return Catalog(m, eq, ex)


@pytest.fixture
async def default_config(db: AsyncSession) -> ModelConfig:
    """Default model config with fractional-set weights (primary 1.0, secondary 0.5)."""
    config = ModelConfig(
        name="test-v1",
        is_default=True,
        role_weights=[
            ConfigRoleWeight(role=P, weight=1.0),
            ConfigRoleWeight(role=S, weight=0.5),
            ConfigRoleWeight(role=MuscleRole.STABILIZER, weight=0.0),
        ],
    )
    db.add(config)
    await db.flush()
    return config
