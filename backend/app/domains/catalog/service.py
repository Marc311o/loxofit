from collections.abc import Collection, Sequence
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
    ExerciseRoles,
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

    async def get_existing_exercise_ids(self, ids: Collection[int]) -> set[int]:
        return await self.repo.existing_exercise_ids(ids)

    async def get_volume_target_muscle_ids(self, ids: Collection[int]) -> set[int]:
        return await self.repo.volume_target_muscle_ids(ids)

    async def get_exercise_roles(self, ids: Collection[int]) -> dict[int, ExerciseRoles]:
        return {
            e.id: ExerciseRoles(
                id=e.id,
                code=e.code,
                is_compound=e.is_compound,
                is_unilateral=e.is_unilateral,
                default_tempo=e.default_tempo,
                roles={r.muscle.code: r.role for r in e.muscle_roles},
            )
            for e in await self.repo.exercises_with_roles(ids)
        }

    async def get_equipment_by_ids(self, ids: Collection[int]) -> list[EquipmentRead]:
        return [EquipmentRead.model_validate(e) for e in await self.repo.equipment_by_ids(ids)]

    async def get_existing_equipment_ids(self, ids: Collection[int]) -> set[int]:
        return await self.repo.existing_equipment_ids(ids)


def get_catalog_service(db: SessionDep, model_configs: ModelConfigServiceDep) -> CatalogService:
    return CatalogService(db, model_configs)


CatalogServiceDep = Annotated[CatalogService, Depends(get_catalog_service)]
