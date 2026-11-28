import uuid
from collections.abc import Sequence

from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domains.plans.enums import PlanStatus
from app.domains.plans.models import Plan, PlanSession, PlanWeek, PrescribedExercise
from app.domains.workouts.enums import WorkoutStatus
from app.domains.workouts.models import LoggedExercise, WorkoutLog

_DETAIL_OPTIONS = (selectinload(WorkoutLog.exercises).selectinload(LoggedExercise.sets),)
_SESSION_OPTIONS = (
    selectinload(PlanSession.week).selectinload(PlanWeek.plan),
    selectinload(PlanSession.exercises.and_(PrescribedExercise.deleted_at.is_(None))),
)
# A session leaves the queue when it was done or skipped; an abandoned one stays.
DONE_STATUSES = (WorkoutStatus.FINISHED, WorkoutStatus.SKIPPED)


class WorkoutRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def add(self, workout: WorkoutLog) -> None:
        self.db.add(workout)

    async def get_for_user(
        self, workout_id: uuid.UUID, user_id: uuid.UUID, *, detail: bool = False
    ) -> WorkoutLog | None:
        stmt = select(WorkoutLog).where(WorkoutLog.id == workout_id, WorkoutLog.user_id == user_id)
        if detail:
            stmt = stmt.options(*_DETAIL_OPTIONS).execution_options(populate_existing=True)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def get_in_progress(self, user_id: uuid.UUID) -> WorkoutLog | None:
        stmt = (
            select(WorkoutLog)
            .where(WorkoutLog.user_id == user_id, WorkoutLog.status == WorkoutStatus.IN_PROGRESS)
            .options(*_DETAIL_OPTIONS)
            .execution_options(populate_existing=True)
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def has_in_progress(self, user_id: uuid.UUID) -> bool:
        stmt = select(
            exists().where(
                WorkoutLog.user_id == user_id, WorkoutLog.status == WorkoutStatus.IN_PROGRESS
            )
        )
        return bool(await self.db.scalar(stmt))

    async def list_finished(
        self, user_id: uuid.UUID, offset: int, limit: int
    ) -> tuple[Sequence[WorkoutLog], int]:
        where = (WorkoutLog.user_id == user_id, WorkoutLog.status == WorkoutStatus.FINISHED)
        total = await self.db.scalar(select(func.count()).select_from(WorkoutLog).where(*where))
        stmt = (
            select(WorkoutLog)
            .where(*where)
            .order_by(WorkoutLog.started_at.desc(), WorkoutLog.id)
            .offset(offset)
            .limit(limit)
        )
        return (await self.db.execute(stmt)).scalars().all(), total or 0

    async def is_session_done(self, plan_session_id: uuid.UUID) -> bool:
        stmt = select(
            exists().where(
                WorkoutLog.plan_session_id == plan_session_id,
                WorkoutLog.status.in_(DONE_STATUSES),
            )
        )
        return bool(await self.db.scalar(stmt))

    async def get_session(
        self, plan_session_id: uuid.UUID, user_id: uuid.UUID, *, active_plan: bool = False
    ) -> PlanSession | None:
        """A session of the user's plan, with its week, plan and current exercises."""
        stmt = (
            select(PlanSession)
            .join(PlanWeek, PlanSession.week_id == PlanWeek.id)
            .join(Plan, PlanWeek.plan_id == Plan.id)
            .where(PlanSession.id == plan_session_id, Plan.user_id == user_id)
            .options(*_SESSION_OPTIONS)
        )
        if active_plan:
            stmt = stmt.where(Plan.status == PlanStatus.ACTIVE)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def get_prescribed(self, prescribed_id: uuid.UUID) -> PrescribedExercise | None:
        return await self.db.get(PrescribedExercise, prescribed_id)
