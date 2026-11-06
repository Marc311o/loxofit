import uuid
from collections.abc import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domains.plans.enums import PlanStatus
from app.domains.plans.models import Plan, PlanSession, PlanWeek, PrescribedExercise

_DETAIL_OPTIONS = (
    selectinload(Plan.weeks)
    .selectinload(PlanWeek.sessions)
    .selectinload(PlanSession.exercises.and_(PrescribedExercise.deleted_at.is_(None))),
    selectinload(Plan.muscle_targets),
)


class PlanRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def add(self, plan: Plan) -> None:
        self.db.add(plan)

    async def delete(self, plan: Plan) -> None:
        await self.db.delete(plan)

    async def list_for_user(self, user_id: uuid.UUID) -> Sequence[Plan]:
        stmt = select(Plan).where(Plan.user_id == user_id).order_by(Plan.updated_at.desc(), Plan.id)
        return (await self.db.execute(stmt)).scalars().all()

    async def get_for_user(
        self, plan_id: uuid.UUID, user_id: uuid.UUID, *, detail: bool = False
    ) -> Plan | None:
        stmt = select(Plan).where(Plan.id == plan_id, Plan.user_id == user_id)
        if detail:
            stmt = stmt.options(*_DETAIL_OPTIONS).execution_options(populate_existing=True)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def get_active_id(self, user_id: uuid.UUID) -> uuid.UUID | None:
        stmt = select(Plan.id).where(Plan.user_id == user_id, Plan.status == PlanStatus.ACTIVE)
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def archive_active(self, user_id: uuid.UUID) -> None:
        stmt = (
            update(Plan)
            .where(Plan.user_id == user_id, Plan.status == PlanStatus.ACTIVE)
            .values(status=PlanStatus.ARCHIVED)
        )
        await self.db.execute(stmt)
