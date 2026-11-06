import uuid
from collections.abc import Iterable

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.users.models import User, UserEquipment, UserProfile


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id: uuid.UUID) -> type[User] | None:
        return await self.db.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        return (await self.db.execute(select(User).where(User.email == email))).scalar_one_or_none()

    def add(self, user: User) -> None:
        self.db.add(user)

    async def get_profile(self, user_id: uuid.UUID) -> UserProfile | None:
        return await self.db.get(UserProfile, user_id)

    def add_profile(self, profile: UserProfile) -> None:
        self.db.add(profile)

    async def list_equipment_ids(self, user_id: uuid.UUID) -> list[int]:
        stmt = select(UserEquipment.equipment_id).where(UserEquipment.user_id == user_id)
        return list((await self.db.execute(stmt)).scalars())

    async def replace_equipment(self, user_id: uuid.UUID, equipment_ids: Iterable[int]) -> None:
        await self.db.execute(delete(UserEquipment).where(UserEquipment.user_id == user_id))
        self.db.add_all(UserEquipment(user_id=user_id, equipment_id=i) for i in equipment_ids)
