import datetime
import uuid
from typing import Annotated

from fastapi import Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionDep
from app.core.security import hash_password
from app.domains.users.enums import UserRole
from app.domains.users.exceptions import EmailAlreadyTakenError
from app.domains.users.models import User
from app.domains.users.repository import UserRepository


def normalize_email(email: str) -> str:
    """Normalizes email"""
    return email.strip().lower()


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = UserRepository(db)

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self.repo.get_by_id(user_id)

    async def get_by_email(self, email: str) -> User | None:
        return await self.repo.get_by_email(normalize_email(email))

    async def create(
        self,
        *,
        email: str,
        password: str,
        display_name: str | None = None,
        role: UserRole = UserRole.USER,
    ) -> User:
        email = normalize_email(email)

        if await self.repo.get_by_email(email) is not None:
            raise EmailAlreadyTakenError()

        user = User(
            email=email, password_hash=hash_password(password), display_name=display_name, role=role
        )

        self.repo.add(user)

        try:
            await self.db.flush()
        except IntegrityError as e:
            await self.db.rollback()
            raise EmailAlreadyTakenError() from e

        return user

    def record_login(self, user: User, *, new_password_hash: str | None = None) -> None:
        user.last_login_at = datetime.datetime.now(datetime.UTC)
        if new_password_hash is not None:
            user.password_hash = new_password_hash


def get_user_service(db: SessionDep) -> UserService:
    return UserService(db)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
