import random
import uuid
from typing import Annotated

from fastapi import Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionDep
from app.domains.catalog.service import CatalogService, CatalogServiceDep
from app.domains.generator.enums import ACTIVE_STATUSES, GenerationStatus
from app.domains.generator.exceptions import (
    GenerationAlreadySavedError,
    GenerationInProgressError,
    GenerationNotDoneError,
    GenerationNotFoundError,
    InvalidGenerationError,
    NoExercisesForSessionError,
)
from app.domains.generator.models import GenerationRun
from app.domains.generator.repository import GenerationRepository
from app.domains.generator.runner import GenerationRunner, RunnerDep
from app.domains.generator.schemas import (
    SEED_MAX,
    GeneratedExercise,
    GeneratedSession,
    GenerationRequest,
    GenerationRunRead,
    SaveGeneratedPlan,
)
from app.domains.model_config.service import ModelConfigService, ModelConfigServiceDep
from app.domains.plans.engine_adapter import build_config, build_spec, build_targets, to_analysis
from app.domains.plans.enums import AnalysisSource
from app.domains.plans.schemas import (
    BaseWeekWrite,
    PlanAnalysis,
    PlanCreate,
    PlanDetail,
    PlanSessionWrite,
    PrescribedExerciseWrite,
)
from app.domains.plans.service import PlanService, PlanServiceDep
from app.domains.users.models import User
from app.domains.users.repository import UserRepository
from app.engine.evaluate import evaluate
from app.engine.generator import (
    CandidateExercise,
    EmptySessionError,
    GenerationTask,
    build_search,
)
from app.engine.progression import build_mesocycle
from app.engine.types import PlannedExercise, Session

ALGORITHM = "hill_climbing"


class GeneratorService:
    def __init__(
        self,
        db: AsyncSession,
        runner: GenerationRunner,
        catalog: CatalogService,
        model_configs: ModelConfigService,
        plans: PlanService,
    ) -> None:
        self.db = db
        self.repo = GenerationRepository(db)
        self.runner = runner
        self.catalog = catalog
        self.model_configs = model_configs
        self.plans = plans

    async def start(self, user: User, request: GenerationRequest) -> GenerationRunRead:
        if await self.repo.has_active(user.id):
            raise GenerationInProgressError()
        task, exercise_ids, config_id = await self._task(user, request)

        run = GenerationRun(
            user_id=user.id,
            config_id=config_id,
            params=request.model_dump(mode="json"),
            seed=task.seed,
            algorithm=ALGORITHM,
            budget=task.budget,
            max_score=max_score,
        )
        self.repo.add(run)
        try:
            await self.db.commit()
        except IntegrityError:  # another request started a run in the meantime
            await self.db.rollback()
            raise GenerationInProgressError() from None

        self.runner.start(run.id, task, exercise_ids)
        return self._read(run)  # no await from here on: the run proceeds on its own session

    async def get(self, user: User, run_id: uuid.UUID) -> GenerationRunRead:
        return self._read(await self._get_owned(user, run_id))

    async def analyze(self, user: User, run_id: uuid.UUID) -> PlanAnalysis:
        """The generated plan scored like a plan - for the preview before saving it."""
        run = await self._get_done(user, run_id)
        request = GenerationRequest.model_validate(run.params)
        assert run.result is not None

        config = await self.model_configs.get(run.config_id)
        engine_config = build_config(config)
        muscles = await self.catalog.list_muscles()
        targets = build_targets(config, muscles, {t.muscle_id: t.priority for t in request.targets})
        ids = {exercise_id for session in run.result for exercise_id, _ in session}
        specs = {i: build_spec(r) for i, r in (await self.catalog.get_exercise_roles(ids)).items()}

        base = tuple(
            Session(
                exercises=tuple(PlannedExercise(specs[i], sets) for i, sets in session),
                max_minutes=spec.max_minutes,
            )
            for session, spec in zip(run.result, request.sessions, strict=True)
        )
        mesocycle = build_mesocycle(base, request.num_weeks, engine_config)
        evaluation = evaluate(mesocycle, targets, engine_config)
        muscle_ids = {m.code: m.id for m in muscles}
        return to_analysis(
            mesocycle, evaluation, targets, engine_config, muscle_ids, AnalysisSource.PROJECTED
        )

    async def save_as_plan(
        self, user: User, run_id: uuid.UUID, data: SaveGeneratedPlan
    ) -> PlanDetail:
        """A draft plan from the generated base week, scored with the generation's config."""
        run = await self._get_done(user, run_id)
        if run.plan_id is not None:
            raise GenerationAlreadySavedError()

        generated = self._read(run)
        assert generated.sessions is not None
        week = BaseWeekWrite(
            sessions=[
                PlanSessionWrite(
                    name=s.name,
                    max_minutes=s.max_minutes,
                    weekday=s.weekday,
                    exercises=[
                        PrescribedExerciseWrite(exercise_id=e.exercise_id, sets=e.sets)
                        for e in s.exercises
                    ],
                )
                for s in generated.sessions
            ]
        )
        request = generated.request
        plan = await self.plans.create_with_base_week(
            user,
            PlanCreate(name=data.name, num_weeks=request.num_weeks),
            run.config_id,
            week,
            request.targets,
        )
        await self.repo.set(run.id, plan_id=plan.id)
        await self.db.commit()
        return plan

    # -- helpers ------------------------------------------------------------

    async def _task(
        self, user: User, request: GenerationRequest
    ) -> tuple[GenerationTask, list[int], int, float]:
        """The engine task, the exercise id of every task index, the config id and the
        max score. Raises before anything is saved when the request cannot be generated."""
        config = await self.model_configs.get_default()
        muscles = await self.catalog.list_muscles()
        priorities = {t.muscle_id: t.priority for t in request.targets}
        if priorities:
            known = await self.catalog.get_volume_target_muscle_ids(set(priorities))
            if missing := sorted(set(priorities) - known):
                raise InvalidGenerationError(f"Unknown or non-target muscle ids: {missing}")

        equipment = set(await UserRepository(self.db).list_equipment_ids(user.id))
        exercises = [
            e for e in await self.catalog.list_generator_exercises() if e.equipment_ids <= equipment
        ]
        task = GenerationTask(
            exercises=tuple(
                CandidateExercise(
                    spec=build_spec(e),
                    complexity=e.complexity,
                    fatigue_cost=e.fatigue_cost,
                    movement_pattern=e.movement_pattern.value,
                )
                for e in exercises
            ),
            focuses=request.focuses(),
            session_minutes=tuple(s.max_minutes for s in request.sessions),
            targets=build_targets(config, muscles, priorities),
            config=build_config(config),
            weeks=request.num_weeks,
            seed=request.seed if request.seed is not None else random.randint(0, SEED_MAX),
        )
        try:  # fail fast: a session no exercise fits
            objective, _ = build_search(
                task.exercises, task.focuses, task.session_minutes,
                task.targets, task.config, task.weeks,
            )  # fmt: skip
        except EmptySessionError as exc:
            focus = task.focuses[exc.session].value
            raise NoExercisesForSessionError(
                f"No exercise with your equipment fits session {exc.session + 1} ({focus})"
            ) from None
        return task, [e.id for e in exercises], config.id, objective.max_score

    async def _get_owned(self, user: User, run_id: uuid.UUID) -> GenerationRun:
        run = await self.repo.get_for_user(run_id, user.id)
        if run is None:
            raise GenerationNotFoundError()
        return run

    async def _get_done(self, user: User, run_id: uuid.UUID) -> GenerationRun:
        run = await self._get_owned(user, run_id)
        if run.status != GenerationStatus.DONE or run.result is None:
            raise GenerationNotDoneError()
        return run

    def _read(self, run: GenerationRun) -> GenerationRunRead:
        request = GenerationRequest.model_validate(run.params)
        sessions = None
        if run.result is not None:
            names, focuses = request.session_names(), request.focuses()
            sessions = [
                GeneratedSession(
                    name=names[k],
                    weekday=spec.weekday,
                    max_minutes=spec.max_minutes,
                    focus=focuses[k],
                    exercises=[GeneratedExercise(exercise_id=i, sets=n) for i, n in session],
                )
                for k, (spec, session) in enumerate(zip(request.sessions, run.result, strict=True))
            ]
        return GenerationRunRead(
            id=run.id,
            status=run.status,
            request=request,
            seed=run.seed,
            algorithm=run.algorithm,
            budget=run.budget,
            config_id=run.config_id,
            progress=self.runner.progress(run.id) if run.status in ACTIVE_STATUSES else None,
            evaluations=run.evaluations,
            score=run.score,
            max_score=run.max_score,
            sessions=sessions,
            history=[(int(e), s) for e, s in run.history] if run.history is not None else None,
            error=run.error,
            plan_id=run.plan_id,
            created_at=run.created_at,
            started_at=run.started_at,
            finished_at=run.finished_at,
        )


def get_generator_service(
    db: SessionDep,
    runner: RunnerDep,
    catalog: CatalogServiceDep,
    model_configs: ModelConfigServiceDep,
    plans: PlanServiceDep,
) -> GeneratorService:
    return GeneratorService(db, runner, catalog, model_configs, plans)


GeneratorServiceDep = Annotated[GeneratorService, Depends(get_generator_service)]
