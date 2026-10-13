from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionDep
from app.core.pagination import Page
from app.domains.catalog.enums import MuscleRole
from app.domains.catalog.exceptions import ExerciseNotFoundError
from app.domains.catalog.models import ExerciseMuscleRole
from app.domains.catalog.repository import CatalogRepository
from app.domains.catalog.schemas import (
    EquipmentFilters,
    EquipmentRead,
    ExerciseDetail,
    ExerciseFilters,
    ExerciseListItem,
    MuscleRead,
    MuscleShare,
)
from app.domains.model_config.service import ModelConfigService, ModelConfigServiceDep


def compute_muscle_shares(
    roles: Sequence[ExerciseMuscleRole], role_weights: dict[MuscleRole, float]
) -> list[MuscleShare]:

    weights = [role_weights.get(r.role, 0.0) for r in roles]
    total = sum(weights)

    shares = [
        MuscleShare(
            muscle=MuscleRead.model_validate(r.muscle),
            role=r.role,
            weight=w,
            share_pct=round(w / total * 100, 1) if total > 0 else 0.0,
        )
        for r, w in zip(roles, weights, strict=True)
    ]

    return sorted(shares, key=lambda s: (-s.share_pct, s.muscle.name_en))


class CatalogService:
    def __init__(self, db: AsyncSession, model_configs: ModelConfigService) -> None:
        self.repo = CatalogRepository(db)
        self.model_configs = model_configs

    async def list_muscles(self) -> list[MuscleRead]:
        return [MuscleRead.model_validate(m) for m in await self.repo.list_muscles()]

    async def list_equipment(self, filters: EquipmentFilters) -> list[EquipmentRead]:
        return [EquipmentRead.model_validate(e) for e in await self.repo.list_equipment(filters)]

    async def list_exercises(self, filters: ExerciseFilters) -> Page[ExerciseListItem]:
        items, total = await self.repo.list_exercises(filters)
        return Page.create([ExerciseListItem.model_validate(e) for e in items], total, filters)

    async def get_exercise(self, exercise_id: int) -> ExerciseDetail:
        exercise = await self.repo.get_exercise_detail(exercise_id)
        if exercise is None:
            raise ExerciseNotFoundError()

        weights = await self.model_configs.get_default_role_weights()
        shares = compute_muscle_shares(exercise.muscle_roles, weights)

        return ExerciseDetail.model_validate(exercise).model_copy(update={"muscles": shares})


def get_catalog_service(db: SessionDep, model_configs: ModelConfigServiceDep) -> CatalogService:
    return CatalogService(db, model_configs)


CatalogServiceDep = Annotated[CatalogService, Depends(get_catalog_service)]
