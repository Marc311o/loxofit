from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domains.model_config.models import ModelConfig


class ModelConfigRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_default(self) -> ModelConfig | None:
        stmt = (
            select(ModelConfig)
            .where(ModelConfig.is_default)
            .options(selectinload(ModelConfig.role_weights))
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()
