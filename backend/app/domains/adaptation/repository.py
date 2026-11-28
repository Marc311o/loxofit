import uuid
from collections.abc import Collection
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import distinct_on
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.adaptation.models import LoadAdjustment


class LoadAdjustmentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def current_weights(
        self, user_id: uuid.UUID, exercise_ids: Collection[int]
    ) -> dict[int, Decimal]:
        """The newest suggested load of every exercise that has one."""
        if not exercise_ids:
            return {}
        stmt = (
            select(LoadAdjustment.exercise_id, LoadAdjustment.weight_kg)
            .where(
                LoadAdjustment.user_id == user_id,
                LoadAdjustment.exercise_id.in_(exercise_ids),
            )
            .order_by(
                LoadAdjustment.exercise_id,
                LoadAdjustment.created_at.desc(),
                LoadAdjustment.id.desc(),
            )
            .ext(distinct_on(LoadAdjustment.exercise_id))
        )
        return {exercise_id: weight for exercise_id, weight in await self.db.execute(stmt)}
