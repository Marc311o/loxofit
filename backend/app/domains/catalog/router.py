from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from app.core.errors import ErrorResponse
from app.core.pagination import Page
from app.domains.auth.dependencies import get_current_user
from app.domains.catalog.enums import MuscleGroup
from app.domains.catalog.schemas import (
    EquipmentFilters,
    EquipmentRead,
    ExerciseDetail,
    ExerciseFilters,
    ExerciseListItem,
    MuscleRead,
)
from app.domains.catalog.service import CatalogServiceDep

router = APIRouter(
    tags=["catalog"],
    dependencies=[Depends(get_current_user)],
    responses={status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse}},
)


@router.get("/muscles")
async def list_muscles(catalog: CatalogServiceDep) -> list[MuscleRead]:
    return await catalog.list_muscles()


@router.get("/equipment")
async def list_equipment(
    catalog: CatalogServiceDep, filters: Annotated[EquipmentFilters, Query()]
) -> list[EquipmentRead]:
    return await catalog.list_equipment(filters)


@router.get("/exercises")
async def list_exercises(
    catalog: CatalogServiceDep, filters: Annotated[ExerciseFilters, Query()]
) -> Page[ExerciseListItem]:
    return await catalog.list_exercises(filters)


@router.get("/exercises/group-counts")
async def count_exercises_by_group(
    catalog: CatalogServiceDep, filters: Annotated[ExerciseFilters, Query()]
) -> dict[MuscleGroup, int]:
    """Exercises per muscle group for the given filters (`muscle_group` itself is ignored)."""
    return await catalog.count_exercises_by_group(filters)


@router.get("/exercises/{exercise_id}")
async def get_exercise(
    exercise_id: Annotated[int, Path(ge=1)], catalog: CatalogServiceDep
) -> ExerciseDetail:
    return await catalog.get_exercise(exercise_id)
