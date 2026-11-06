import uuid

from fastapi import APIRouter, status

from app.core.errors import ErrorResponse
from app.domains.auth.dependencies import CurrentUser
from app.domains.plans.schemas import (
    BaseWeekWrite,
    MuscleTargetsWrite,
    PlanCreate,
    PlanDetail,
    PlanSummary,
    PlanUpdate,
)
from app.domains.plans.service import PlanServiceDep

router = APIRouter(
    prefix="/plans",
    tags=["plans"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
    },
)

_CONFLICT = {status.HTTP_409_CONFLICT: {"model": ErrorResponse}}


@router.get("")
async def list_plans(user: CurrentUser, plans: PlanServiceDep) -> list[PlanSummary]:
    return await plans.list_plans(user)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_plan(data: PlanCreate, user: CurrentUser, plans: PlanServiceDep) -> PlanDetail:
    return await plans.create(user, data)


@router.get("/active")
async def get_active_plan(user: CurrentUser, plans: PlanServiceDep) -> PlanDetail:
    return await plans.get_active(user)


@router.get("/{plan_id}")
async def get_plan(plan_id: uuid.UUID, user: CurrentUser, plans: PlanServiceDep) -> PlanDetail:
    return await plans.get_plan(user, plan_id)


@router.patch("/{plan_id}", responses=_CONFLICT)
async def update_plan(
    plan_id: uuid.UUID, data: PlanUpdate, user: CurrentUser, plans: PlanServiceDep
) -> PlanDetail:
    return await plans.update(user, plan_id, data)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(plan_id: uuid.UUID, user: CurrentUser, plans: PlanServiceDep) -> None:
    await plans.delete(user, plan_id)


@router.post("/{plan_id}/activate", responses=_CONFLICT)
async def activate_plan(plan_id: uuid.UUID, user: CurrentUser, plans: PlanServiceDep) -> PlanDetail:
    return await plans.activate(user, plan_id)


@router.put("/{plan_id}/base-week", responses=_CONFLICT)
async def replace_base_week(
    plan_id: uuid.UUID, data: BaseWeekWrite, user: CurrentUser, plans: PlanServiceDep
) -> PlanDetail:
    return await plans.replace_base_week(user, plan_id, data)


@router.put("/{plan_id}/muscle-targets", responses=_CONFLICT)
async def set_muscle_targets(
    plan_id: uuid.UUID, data: MuscleTargetsWrite, user: CurrentUser, plans: PlanServiceDep
) -> PlanDetail:
    return await plans.set_muscle_targets(user, plan_id, data)
