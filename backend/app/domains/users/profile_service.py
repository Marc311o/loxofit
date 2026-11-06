from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionDep
from app.domains.catalog.schemas import EquipmentRead
from app.domains.catalog.service import CatalogService, CatalogServiceDep
from app.domains.users.exceptions import InvalidEquipmentError, ProfileNotFoundError
from app.domains.users.models import User, UserProfile
from app.domains.users.repository import UserRepository
from app.domains.users.schemas import (
    EquipmentIdsWrite,
    ProfileRead,
    ProfileWrite,
    UserRead,
    UserUpdate,
)


class ProfileService:
    """Self-service part of the users domain: profile, equipment, display name."""

    def __init__(self, db: AsyncSession, catalog: CatalogService) -> None:
        self.db = db
        self.repo = UserRepository(db)
        self.catalog = catalog

    async def update_user(self, user: User, data: UserUpdate) -> UserRead:
        if "display_name" in data.model_fields_set:
            user.display_name = data.display_name
        await self.db.commit()
        return UserRead.model_validate(user)

    async def get_profile(self, user: User) -> ProfileRead:
        profile = await self.repo.get_profile(user.id)
        if profile is None:
            raise ProfileNotFoundError()
        return ProfileRead.model_validate(profile)

    async def put_profile(self, user: User, data: ProfileWrite) -> ProfileRead:
        profile = await self.repo.get_profile(user.id)
        if profile is None:
            profile = UserProfile(user_id=user.id)
            self.repo.add_profile(profile)
        for field, value in data.model_dump().items():
            setattr(profile, field, value)
        await self.db.commit()
        return ProfileRead.model_validate(profile)

    async def get_equipment(self, user: User) -> list[EquipmentRead]:
        ids = await self.repo.list_equipment_ids(user.id)
        return await self.catalog.get_equipment_by_ids(ids) if ids else []

    async def set_equipment(self, user: User, data: EquipmentIdsWrite) -> list[EquipmentRead]:
        ids = set(data.equipment_ids)
        missing = ids - await self.catalog.get_existing_equipment_ids(ids) if ids else set()
        if missing:
            raise InvalidEquipmentError(f"Unknown equipment ids: {sorted(missing)}")
        await self.repo.replace_equipment(user.id, ids)
        await self.db.commit()
        return await self.get_equipment(user)


def get_profile_service(db: SessionDep, catalog: CatalogServiceDep) -> ProfileService:
    return ProfileService(db, catalog)


ProfileServiceDep = Annotated[ProfileService, Depends(get_profile_service)]
