import uuid
from datetime import UTC, datetime
from typing import Annotated, TypeVar

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionDep
from app.domains.catalog.service import CatalogService, CatalogServiceDep
from app.domains.model_config.service import ModelConfigService, ModelConfigServiceDep
from app.domains.plans.enums import PlanStatus
from app.domains.plans.exceptions import (
    InvalidPlanError,
    NoActivePlanError,
    PlanArchivedError,
    PlanIncompleteError,
    PlanNotFoundError,
)
from app.domains.plans.models import (
    Plan,
    PlanMuscleTarget,
    PlanSession,
    PlanWeek,
    PrescribedExercise,
)
from app.domains.plans.repository import PlanRepository
from app.domains.plans.schemas import (
    BaseWeekWrite,
    MuscleTargetsWrite,
    PlanCreate,
    PlanDetail,
    PlanSummary,
    PlanUpdate,
    PrescribedExerciseWrite,
)
from app.domains.users.models import User

T = TypeVar("T")


def _take(items: dict[uuid.UUID, T], key: uuid.UUID, kind: str) -> T:
    """Pops an existing child by id; an id that is not in the plan is a client error."""
    try:
        return items.pop(key)
    except KeyError:
        raise InvalidPlanError(f"Unknown {kind} id: {key}") from None


class PlanService:
    def __init__(
        self, db: AsyncSession, model_configs: ModelConfigService, catalog: CatalogService
    ) -> None:
        self.db = db
        self.repo = PlanRepository(db)
        self.model_configs = model_configs
        self.catalog = catalog

    # -- queries ------------------------------------------------------------

    async def list_plans(self, user: User) -> list[PlanSummary]:
        return [PlanSummary.model_validate(p) for p in await self.repo.list_for_user(user.id)]

    async def get_plan(self, user: User, plan_id: uuid.UUID) -> PlanDetail:
        return PlanDetail.model_validate(await self._get_owned(user, plan_id, detail=True))

    async def get_active(self, user: User) -> PlanDetail:
        plan_id = await self.repo.get_active_id(user.id)
        if plan_id is None:
            raise NoActivePlanError()
        return await self.get_plan(user, plan_id)

    # -- commands -----------------------------------------------------------

    async def create(self, user: User, data: PlanCreate) -> PlanDetail:
        config = await self.model_configs.get_default()
        plan = Plan(
            user_id=user.id,
            config_id=config.id,
            name=data.name,
            num_weeks=data.num_weeks,
            weeks=[PlanWeek(week_number=1, rir=config.rir_start, sessions=[])],
            muscle_targets=[],
        )
        self.repo.add(plan)
        await self.db.commit()
        return await self.get_plan(user, plan.id)

    async def update(self, user: User, plan_id: uuid.UUID, data: PlanUpdate) -> PlanDetail:
        plan = await self._get_editable(user, plan_id)
        if data.name is not None:
            plan.name = data.name
        if data.num_weeks is not None and data.num_weeks != plan.num_weeks:
            plan.num_weeks = data.num_weeks
            self._drop_generated_weeks(plan)
        await self._save(plan)
        return await self.get_plan(user, plan.id)

    async def delete(self, user: User, plan_id: uuid.UUID) -> None:
        plan = await self._get_owned(user, plan_id)
        await self.repo.delete(plan)
        await self.db.commit()

    async def activate(self, user: User, plan_id: uuid.UUID) -> PlanDetail:
        plan = await self._get_owned(user, plan_id, detail=True)
        if plan.status != PlanStatus.ACTIVE:
            if len(plan.weeks) != plan.num_weeks:
                raise PlanIncompleteError()
            await self.repo.archive_active(user.id)
            plan.status = PlanStatus.ACTIVE
            await self._save(plan)
        return await self.get_plan(user, plan.id)

    async def replace_base_week(
        self, user: User, plan_id: uuid.UUID, data: BaseWeekWrite
    ) -> PlanDetail:
        plan = await self._get_editable(user, plan_id)
        await self._ensure_exercises_exist(data)

        week = plan.weeks[0]
        existing = {s.id: s for s in week.sessions}
        sessions: list[PlanSession] = []
        for position, s_in in enumerate(data.sessions, start=1):
            if s_in.id is None:
                session = PlanSession(exercises=[])
            else:
                session = _take(existing, s_in.id, "session")
            session.position = position
            session.name = s_in.name
            session.max_minutes = s_in.max_minutes
            session.weekday = s_in.weekday
            self._sync_exercises(session, s_in.exercises)
            sessions.append(session)

        week.sessions = sessions
        self._drop_generated_weeks(plan)
        await self._save(plan)
        return await self.get_plan(user, plan.id)

    async def set_muscle_targets(
        self, user: User, plan_id: uuid.UUID, data: MuscleTargetsWrite
    ) -> PlanDetail:
        plan = await self._get_editable(user, plan_id)
        ids = {t.muscle_id for t in data.targets}
        missing = ids - await self.catalog.get_volume_target_muscle_ids(ids)
        if missing:
            raise InvalidPlanError(f"Unknown or non-target muscle ids: {sorted(missing)}")

        plan.muscle_targets = [
            PlanMuscleTarget(muscle_id=t.muscle_id, priority=t.priority)
            for t in data.targets
            if t.priority != 1.0
        ]
        await self._save(plan)
        return await self.get_plan(user, plan.id)

    # -- helpers ------------------------------------------------------------

    async def _get_owned(self, user: User, plan_id: uuid.UUID, *, detail: bool = False) -> Plan:
        plan = await self.repo.get_for_user(plan_id, user.id, detail=detail)
        if plan is None:
            raise PlanNotFoundError()
        return plan

    async def _get_editable(self, user: User, plan_id: uuid.UUID) -> Plan:
        plan = await self._get_owned(user, plan_id, detail=True)
        if plan.status == PlanStatus.ARCHIVED:
            raise PlanArchivedError()
        return plan

    async def _save(self, plan: Plan) -> None:
        plan.updated_at = datetime.now(UTC)
        await self.db.commit()

    async def _ensure_exercises_exist(self, data: BaseWeekWrite) -> None:
        ids = {e.exercise_id for s in data.sessions for e in s.exercises}
        if not ids:
            return
        missing = ids - await self.catalog.get_existing_exercise_ids(ids)
        if missing:
            raise InvalidPlanError(f"Unknown exercise ids: {sorted(missing)}")

    @staticmethod
    def _drop_generated_weeks(plan: Plan) -> None:
        """Weeks 2..n are derived from week 1 and must be regenerated after it changes."""
        plan.weeks[:] = [w for w in plan.weeks if w.week_number == 1]

    @staticmethod
    def _sync_exercises(session: PlanSession, items: list[PrescribedExerciseWrite]) -> None:
        now = datetime.now(UTC)
        existing = {e.id: e for e in session.exercises}
        for slot, e_in in enumerate(items, start=1):
            current = _take(existing, e_in.id, "exercise entry") if e_in.id else None
            if current is not None and current.exercise_id != e_in.exercise_id:
                current.deleted_at = now
                current = None
            if current is None:
                current = PrescribedExercise(exercise_id=e_in.exercise_id)
                session.exercises.append(current)
            current.slot = slot
            current.sets = e_in.sets
            current.rep_min = e_in.rep_min
            current.rep_max = e_in.rep_max
        for removed in existing.values():
            removed.deleted_at = now


def get_plan_service(
    db: SessionDep, model_configs: ModelConfigServiceDep, catalog: CatalogServiceDep
) -> PlanService:
    return PlanService(db, model_configs, catalog)


PlanServiceDep = Annotated[PlanService, Depends(get_plan_service)]
