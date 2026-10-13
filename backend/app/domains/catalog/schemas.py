from pydantic import BaseModel, ConfigDict, Field

from app.core.pagination import PageParams
from app.domains.catalog.enums import (
    EquipmentCategory,
    EquipmentSort,
    ExerciseSort,
    MovementPattern,
    MuscleGroup,
    MuscleRole,
)


class ORMSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MuscleRead(ORMSchema):
    id: int
    code: str
    name_pl: str
    name_en: str
    muscle_group: MuscleGroup
    is_volume_target: bool


class EquipmentRead(ORMSchema):
    id: int
    name_en: str
    name_pl: str
    category: EquipmentCategory


class ExerciseListItem(ORMSchema):
    id: int
    name_en: str
    name_pl: str
    main_group: MuscleGroup
    movement_pattern: MovementPattern
    is_compound: bool
    is_unilateral: bool
    equipment: list[EquipmentRead]


class MuscleShare(ORMSchema):
    muscle: MuscleRead
    role: MuscleRole
    weight: float
    share_pct: float


class ExerciseDetail(ExerciseListItem):
    fatigue_cost: int
    complexity: int
    default_tempo: str | None
    instructions_pl: str | None
    instructions_en: str | None
    muscles: list[MuscleShare] = []


class ExerciseFilters(PageParams):
    model_config = ConfigDict(extra="forbid")

    muscle_group: MuscleGroup | None
    pattern: MovementPattern | None
    muscle_id: int | None = Field(ge=1)
    equipment_id: int | None = Field(ge=1)
    search: str | None = Field(min_length=1, max_length=100, default=None)
    sort: ExerciseSort = ExerciseSort.NAME_EN


class EquipmentFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: EquipmentCategory | None = None
    search: str | None = Field(min_length=1, max_length=100, default=None)
    sort: EquipmentSort = EquipmentSort.CATEGORY
