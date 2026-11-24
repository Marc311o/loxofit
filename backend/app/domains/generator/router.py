import uuid

from fastapi import APIRouter, status

from app.core.errors import ErrorResponse
from app.domains.auth.dependencies import CurrentUser
from app.domains.generator.schemas import GenerationRequest, GenerationRunRead, SaveGeneratedPlan
from app.domains.generator.service import GeneratorServiceDep
from app.domains.plans.schemas import PlanAnalysis, PlanDetail

router = APIRouter(
    prefix="/generator",
    tags=["generator"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
    },
)

_CONFLICT = {status.HTTP_409_CONFLICT: {"model": ErrorResponse}}


@router.post(
    "/runs",
    status_code=status.HTTP_202_ACCEPTED,
    responses={**_CONFLICT, 422: {"model": ErrorResponse}},
)
async def start_generation(
    data: GenerationRequest, user: CurrentUser, generator: GeneratorServiceDep
) -> GenerationRunRead:
    """Starts a generation in the background - poll GET /runs/{id} for its progress."""
    return await generator.start(user, data)


@router.get("/runs/{run_id}")
async def get_generation(
    run_id: uuid.UUID, user: CurrentUser, generator: GeneratorServiceDep
) -> GenerationRunRead:
    return await generator.get(user, run_id)


@router.get("/runs/{run_id}/analysis", responses=_CONFLICT)
async def analyze_generation(
    run_id: uuid.UUID, user: CurrentUser, generator: GeneratorServiceDep
) -> PlanAnalysis:
    return await generator.analyze(user, run_id)


@router.post("/runs/{run_id}/plan", status_code=status.HTTP_201_CREATED, responses=_CONFLICT)
async def save_generation_as_plan(
    run_id: uuid.UUID, data: SaveGeneratedPlan, user: CurrentUser, generator: GeneratorServiceDep
) -> PlanDetail:
    return await generator.save_as_plan(user, run_id, data)
