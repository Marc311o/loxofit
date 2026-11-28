import uuid
from typing import Annotated

from fastapi import APIRouter, Path, status

from app.core.errors import ErrorResponse
from app.core.pagination import Page, PageParamsDep
from app.domains.auth.dependencies import CurrentUser
from app.domains.workouts.schemas import (
    MAX_SETS_PER_EXERCISE,
    ExerciseReplace,
    SetWrite,
    WorkoutDetail,
    WorkoutFinish,
    WorkoutStart,
    WorkoutSummary,
)
from app.domains.workouts.service import WorkoutServiceDep

router = APIRouter(
    prefix="/workouts",
    tags=["workouts"],
    responses={status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse}},
)

_NOT_FOUND = {status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}}
_CONFLICT = {status.HTTP_409_CONFLICT: {"model": ErrorResponse}}
SetNumber = Annotated[int, Path(ge=1, le=MAX_SETS_PER_EXERCISE)]


@router.get("")
async def list_workouts(
    user: CurrentUser, workouts: WorkoutServiceDep, page: PageParamsDep
) -> Page[WorkoutSummary]:
    """Finished workouts, newest first."""
    return await workouts.list_finished(user, page)


@router.post("", status_code=status.HTTP_201_CREATED, responses={**_NOT_FOUND, **_CONFLICT})
async def start_workout(
    data: WorkoutStart, user: CurrentUser, workouts: WorkoutServiceDep
) -> WorkoutDetail:
    return await workouts.start(user, data)


@router.get("/current", responses=_NOT_FOUND)
async def get_current_workout(user: CurrentUser, workouts: WorkoutServiceDep) -> WorkoutDetail:
    return await workouts.get_current(user)


@router.get("/{workout_id}", responses=_NOT_FOUND)
async def get_workout(
    workout_id: uuid.UUID, user: CurrentUser, workouts: WorkoutServiceDep
) -> WorkoutDetail:
    return await workouts.get(user, workout_id)


@router.put(
    "/{workout_id}/exercises/{logged_id}/sets/{set_number}",
    responses={**_NOT_FOUND, **_CONFLICT},
)
async def save_set(
    workout_id: uuid.UUID,
    logged_id: uuid.UUID,
    set_number: SetNumber,
    data: SetWrite,
    user: CurrentUser,
    workouts: WorkoutServiceDep,
) -> WorkoutDetail:
    return await workouts.save_set(user, workout_id, logged_id, set_number, data)


@router.delete(
    "/{workout_id}/exercises/{logged_id}/sets/{set_number}",
    responses={**_NOT_FOUND, **_CONFLICT},
)
async def delete_set(
    workout_id: uuid.UUID,
    logged_id: uuid.UUID,
    set_number: SetNumber,
    user: CurrentUser,
    workouts: WorkoutServiceDep,
) -> WorkoutDetail:
    return await workouts.delete_set(user, workout_id, logged_id, set_number)


@router.put("/{workout_id}/exercises/{logged_id}/exercise", responses={**_NOT_FOUND, **_CONFLICT})
async def replace_exercise(
    workout_id: uuid.UUID,
    logged_id: uuid.UUID,
    data: ExerciseReplace,
    user: CurrentUser,
    workouts: WorkoutServiceDep,
) -> WorkoutDetail:
    return await workouts.replace_exercise(user, workout_id, logged_id, data)


@router.post("/{workout_id}/finish", responses={**_NOT_FOUND, **_CONFLICT})
async def finish_workout(
    workout_id: uuid.UUID, data: WorkoutFinish, user: CurrentUser, workouts: WorkoutServiceDep
) -> WorkoutDetail:
    return await workouts.finish(user, workout_id, data)


@router.post("/{workout_id}/abandon", responses={**_NOT_FOUND, **_CONFLICT})
async def abandon_workout(
    workout_id: uuid.UUID, user: CurrentUser, workouts: WorkoutServiceDep
) -> WorkoutDetail:
    return await workouts.abandon(user, workout_id)
