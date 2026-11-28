"""Workouts: start one from a session of the active plan, log its sets, finish it.

A workout copies its targets when it starts; the plan's later edits do not change it.
"""

import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated

from fastapi import Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionDep
from app.core.pagination import Page, PageParams
from app.domains.adaptation.repository import LoadAdjustmentRepository
from app.domains.catalog.exceptions import ExerciseNotFoundError
from app.domains.catalog.service import CatalogService, CatalogServiceDep
from app.domains.model_config.service import ModelConfigService, ModelConfigServiceDep
from app.domains.plans.engine_adapter import build_config, build_spec
from app.domains.plans.models import PlanSession
from app.domains.users.models import User
from app.domains.users.repository import UserRepository
from app.domains.workouts.enums import WorkoutStatus
from app.domains.workouts.exceptions import (
    ExerciseHasSetsError,
    LoggedExerciseNotFoundError,
    NoWorkoutInProgressError,
    SessionAlreadyDoneError,
    SessionNotFoundError,
    SetNotFoundError,
    WorkoutEmptyError,
    WorkoutInProgressError,
    WorkoutNotFoundError,
    WorkoutNotInProgressError,
)
from app.domains.workouts.models import LoggedExercise, LoggedSet, WorkoutLog
from app.domains.workouts.repository import WorkoutRepository
from app.domains.workouts.schemas import (
    ExerciseReplace,
    LoggedExerciseRead,
    LoggedSetRead,
    SetWrite,
    WorkoutDetail,
    WorkoutFinish,
    WorkoutStart,
    WorkoutSummary,
)
from app.engine.timing import needs_warmup, rep_range, rest_s
from app.engine.types import EngineConfig, ExerciseSpec


def _target_reps(
    rep_min: int | None, rep_max: int | None, spec: ExerciseSpec, config: EngineConfig
) -> tuple[int, int]:
    """The prescribed rep range; what the plan leaves open comes from the engine's default."""
    low, high = rep_range(spec, config)
    return rep_min or low, rep_max or high


class WorkoutService:
    def __init__(
        self, db: AsyncSession, model_configs: ModelConfigService, catalog: CatalogService
    ) -> None:
        self.db = db
        self.repo = WorkoutRepository(db)
        self.loads = LoadAdjustmentRepository(db)
        self.users = UserRepository(db)
        self.model_configs = model_configs
        self.catalog = catalog

    # -- queries ------------------------------------------------------------

    async def get_current(self, user: User) -> WorkoutDetail:
        workout = await self.repo.get_in_progress(user.id)
        if workout is None:
            raise NoWorkoutInProgressError()
        return await self._detail(user, workout)

    async def get(self, user: User, workout_id: uuid.UUID) -> WorkoutDetail:
        return await self._detail(user, await self._get_owned(user, workout_id))

    async def list_finished(self, user: User, params: PageParams) -> Page[WorkoutSummary]:
        items, total = await self.repo.list_finished(user.id, params.offset, params.size)
        return Page.create([WorkoutSummary.model_validate(w) for w in items], total, params)

    # -- commands -----------------------------------------------------------

    async def start(self, user: User, data: WorkoutStart) -> WorkoutDetail:
        if await self.repo.has_in_progress(user.id):
            raise WorkoutInProgressError()
        session = await self.repo.get_session(data.plan_session_id, user.id, active_plan=True)
        if session is None:
            raise SessionNotFoundError()
        if await self.repo.is_session_done(session.id):
            raise SessionAlreadyDoneError()

        config, specs = await self._engine_context(
            session, [e.exercise_id for e in session.exercises]
        )
        loads = await self.loads.current_weights(user.id, specs.keys())
        profile = await self.users.get_profile(user.id)
        body_weight = profile.weight_kg if profile else None

        workout = WorkoutLog(
            user_id=user.id,
            plan_session_id=session.id,
            session_name=session.name,
            body_weight_kg=round(Decimal(str(body_weight)), 2) if body_weight else None,
            exercises=[],
        )
        for position, p in enumerate(session.exercises, start=1):
            low, high = _target_reps(p.rep_min, p.rep_max, specs[p.exercise_id], config)
            workout.exercises.append(
                LoggedExercise(
                    position=position,
                    prescribed_exercise_id=p.id,
                    exercise_id=p.exercise_id,
                    target_sets=p.sets,
                    target_rep_min=low,
                    target_rep_max=high,
                    target_rir=session.week.rir,
                    suggested_weight_kg=loads.get(p.exercise_id),
                    sets=[],
                )
            )
        self.repo.add(workout)
        try:
            await self.db.commit()
        except IntegrityError:  # another start won the race for the one in-progress slot
            await self.db.rollback()
            raise WorkoutInProgressError() from None
        return await self.get(user, workout.id)

    async def save_set(
        self,
        user: User,
        workout_id: uuid.UUID,
        logged_id: uuid.UUID,
        set_number: int,
        data: SetWrite,
    ) -> WorkoutDetail:
        """Creates or corrects set `set_number` - repeating the same request changes nothing."""
        workout = await self._get_open(user, workout_id)
        exercise = self._exercise(workout, logged_id)
        current = next((s for s in exercise.sets if s.set_number == set_number), None)
        if current is None:
            current = LoggedSet(set_number=set_number, completed_at=datetime.now(UTC))
            exercise.sets.append(current)
        current.weight_kg = data.weight_kg
        current.reps = data.reps
        current.rir = data.rir
        await self.db.commit()
        return await self.get(user, workout.id)

    async def delete_set(
        self, user: User, workout_id: uuid.UUID, logged_id: uuid.UUID, set_number: int
    ) -> WorkoutDetail:
        workout = await self._get_open(user, workout_id)
        exercise = self._exercise(workout, logged_id)
        current = next((s for s in exercise.sets if s.set_number == set_number), None)
        if current is None:
            raise SetNotFoundError()
        exercise.sets.remove(current)
        await self.db.commit()
        return await self.get(user, workout.id)

    async def replace_exercise(
        self, user: User, workout_id: uuid.UUID, logged_id: uuid.UUID, data: ExerciseReplace
    ) -> WorkoutDetail:
        """Another exercise in this workout only - the plan stays as it is."""
        workout = await self._get_open(user, workout_id)
        exercise = self._exercise(workout, logged_id)
        if exercise.exercise_id == data.exercise_id:
            return await self._detail(user, workout)
        if exercise.sets:
            raise ExerciseHasSetsError()
        if not await self.catalog.get_existing_exercise_ids({data.exercise_id}):
            raise ExerciseNotFoundError()

        prescribed = (
            await self.repo.get_prescribed(exercise.prescribed_exercise_id)
            if exercise.prescribed_exercise_id
            else None
        )
        session = await self._session(user, workout)
        if prescribed is not None and session is not None:
            config, specs = await self._engine_context(session, [data.exercise_id])
            exercise.target_rep_min, exercise.target_rep_max = _target_reps(
                prescribed.rep_min, prescribed.rep_max, specs[data.exercise_id], config
            )
        loads = await self.loads.current_weights(user.id, [data.exercise_id])
        exercise.exercise_id = data.exercise_id
        exercise.suggested_weight_kg = loads.get(data.exercise_id)
        await self.db.commit()
        return await self.get(user, workout.id)

    async def finish(self, user: User, workout_id: uuid.UUID, data: WorkoutFinish) -> WorkoutDetail:
        workout = await self._get_open(user, workout_id)
        if not any(e.sets for e in workout.exercises):
            raise WorkoutEmptyError()
        workout.status = WorkoutStatus.FINISHED
        workout.finished_at = datetime.now(UTC)
        workout.session_rpe = data.session_rpe
        workout.notes = data.notes
        await self.db.commit()
        return await self.get(user, workout.id)

    async def abandon(self, user: User, workout_id: uuid.UUID) -> WorkoutDetail:
        """Ends the workout without counting it - its session stays in the queue."""
        workout = await self._get_open(user, workout_id)
        workout.status = WorkoutStatus.ABANDONED
        workout.finished_at = datetime.now(UTC)
        await self.db.commit()
        return await self.get(user, workout.id)

    # -- helpers ------------------------------------------------------------

    async def _get_owned(self, user: User, workout_id: uuid.UUID) -> WorkoutLog:
        workout = await self.repo.get_for_user(workout_id, user.id, detail=True)
        if workout is None:
            raise WorkoutNotFoundError()
        return workout

    async def _get_open(self, user: User, workout_id: uuid.UUID) -> WorkoutLog:
        workout = await self._get_owned(user, workout_id)
        if workout.status != WorkoutStatus.IN_PROGRESS:
            raise WorkoutNotInProgressError()
        return workout

    @staticmethod
    def _exercise(workout: WorkoutLog, logged_id: uuid.UUID) -> LoggedExercise:
        exercise = next((e for e in workout.exercises if e.id == logged_id), None)
        if exercise is None:
            raise LoggedExerciseNotFoundError()
        return exercise

    async def _session(self, user: User, workout: WorkoutLog) -> PlanSession | None:
        if workout.plan_session_id is None:
            return None
        return await self.repo.get_session(workout.plan_session_id, user.id)

    async def _engine_context(
        self, session: PlanSession, exercise_ids: list[int]
    ) -> tuple[EngineConfig, dict[int, ExerciseSpec]]:
        config = build_config(await self.model_configs.get(session.week.plan.config_id))
        roles = await self.catalog.get_exercise_roles(exercise_ids) if exercise_ids else {}
        return config, {exercise_id: build_spec(r) for exercise_id, r in roles.items()}

    async def _detail(self, user: User, workout: WorkoutLog) -> WorkoutDetail:
        session = await self._session(user, workout)
        ids = [e.exercise_id for e in workout.exercises]
        if session is not None:
            config, specs = await self._engine_context(session, ids)
        else:  # the plan is gone - no config to take the rest times from
            config = None
            roles = await self.catalog.get_exercise_roles(ids) if ids else {}
            specs = {exercise_id: build_spec(r) for exercise_id, r in roles.items()}

        return WorkoutDetail(
            id=workout.id,
            status=workout.status,
            session_name=workout.session_name,
            plan_session_id=workout.plan_session_id,
            started_at=workout.started_at,
            finished_at=workout.finished_at,
            session_rpe=workout.session_rpe,
            week_number=session.week.week_number if session else None,
            is_deload=session.week.is_deload if session else None,
            body_weight_kg=workout.body_weight_kg,
            notes=workout.notes,
            exercises=_exercises(workout.exercises, specs, config),
        )


def _exercises(
    exercises: list[LoggedExercise],
    specs: Mapping[int, ExerciseSpec],
    config: EngineConfig | None,
) -> list[LoggedExerciseRead]:
    """Rest and warm-up as the engine assumes them when it estimates the session's time."""
    result = []
    trained_primary: set[str] = set()
    for e in exercises:
        spec = specs[e.exercise_id]
        result.append(
            LoggedExerciseRead(
                id=e.id,
                position=e.position,
                exercise_id=e.exercise_id,
                prescribed_exercise_id=e.prescribed_exercise_id,
                target_sets=e.target_sets,
                target_rep_min=e.target_rep_min,
                target_rep_max=e.target_rep_max,
                target_rir=e.target_rir,
                suggested_weight_kg=e.suggested_weight_kg,
                rest_seconds=rest_s(spec, config) if config else None,
                warm_up=needs_warmup(spec, trained_primary),
                sets=[LoggedSetRead.model_validate(s) for s in e.sets],
            )
        )
        if spec.is_compound:
            trained_primary |= spec.primary_muscles()
    return result


def get_workout_service(
    db: SessionDep, model_configs: ModelConfigServiceDep, catalog: CatalogServiceDep
) -> WorkoutService:
    return WorkoutService(db, model_configs, catalog)


WorkoutServiceDep = Annotated[WorkoutService, Depends(get_workout_service)]
