import uuid
from typing import Any

from sqlalchemy import exists, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.generator.enums import ACTIVE_STATUSES, GenerationStatus
from app.domains.generator.models import GenerationRun


class GenerationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def add(self, run: GenerationRun) -> None:
        self.db.add(run)

    async def get_for_user(self, run_id: uuid.UUID, user_id: uuid.UUID) -> GenerationRun | None:
        # The run is updated in the background - always read its current state.
        stmt = (
            select(GenerationRun)
            .where(GenerationRun.id == run_id, GenerationRun.user_id == user_id)
            .execution_options(populate_existing=True)
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def has_active(self, user_id: uuid.UUID) -> bool:
        stmt = select(
            exists().where(
                GenerationRun.user_id == user_id, GenerationRun.status.in_(ACTIVE_STATUSES)
            )
        )
        return bool(await self.db.scalar(stmt))

    async def set(self, run_id: uuid.UUID, **values: Any) -> None:
        await self.db.execute(
            update(GenerationRun).where(GenerationRun.id == run_id).values(**values)
        )

    async def fail_interrupted(self) -> int:
        """Runs that were queued or running when the server stopped will never finish."""
        result = await self.db.execute(
            update(GenerationRun)
            .where(GenerationRun.status.in_(ACTIVE_STATUSES))
            .values(status=GenerationStatus.FAILED, error="Interrupted by a server restart")
        )
        return result.rowcount
