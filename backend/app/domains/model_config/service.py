import logging
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionDep
from app.domains.catalog.enums import MuscleRole
from app.domains.model_config.exceptions import DefaultConfigMissingError
from app.domains.model_config.repository import ModelConfigRepository

logger = logging.getLogger(__name__)


class ModelConfigService:
    def __init__(self, db: AsyncSession):
        self.repo = ModelConfigRepository(db)

    async def get_default(self):
        config = await self.repo.get_default()
        if config is None:
            logger.error("No default model config in database")
            raise DefaultConfigMissingError()
        return config

    async def get_default_role_weights(self) -> dict[MuscleRole, float]:
        config = await self.get_default()
        return {rw.role: rw.weight for rw in config.role_weights}


def get_model_config_service(db: SessionDep) -> ModelConfigService:
    return ModelConfigService(db)


ModelConfigServiceDep = Annotated[ModelConfigService, Depends(get_model_config_service)]
