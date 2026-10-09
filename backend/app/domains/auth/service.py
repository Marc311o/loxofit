import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
    refresh_token_expires_at,
    verify_and_update_password,
    verify_password,
)
from app.domains.auth.exceptions import (
    InactiveAccountError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
)
from app.domains.auth.models import RefreshToken
from app.domains.auth.repository import RefreshTokenRepository
from app.domains.auth.schemas import RegisterRequest
from app.domains.users.models import User
from app.domains.users.service import UserService

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class IssuedTokens:
    access_token: str
    refresh_token: str
    expires_in: int


class AuthService:
    def __init__(self, db: AsyncSession, users: UserService) -> None:
        self.db = db
        self.users = users
        self.tokens = RefreshTokenRepository(db)

    async def register(self, data: RegisterRequest) -> User:
        user = await self.users.create(
            email=data.email, password=data.password, display_name=data.display_name
        )

        await self.db.commit()
        return user

    async def login(self, email: str, password: str) -> IssuedTokens:
        user = await self.users.get_by_email(email)

        if user is None:
            verify_password(password, None)
            raise InvalidCredentialsError()

        is_valid, new_hash = verify_and_update_password(password, user.password_hash)
        if not is_valid:
            raise InvalidCredentialsError()

        if not user.is_active:
            raise InactiveAccountError()

        self.users.record_login(user, new_password_hash=new_hash)
        tokens = self._issue_tokens(user)
        await self.db.commit()

        return tokens

    async def refresh(self, raw_token: str | None) -> IssuedTokens:

        if not raw_token:
            raise InvalidRefreshTokenError()

        stored = await self.tokens.get_by_hash(hash_refresh_token(raw_token), for_update=True)
        if stored is None:
            raise InvalidRefreshTokenError()

        now = datetime.now(UTC)

        if stored.revoked_at is not None:
            logger.warning(
                f"Repeated usage of refresh token (user {stored.user_id}) - cancelling session"
            )
            await self.tokens.revoke_all_for_user(stored.user_id, now)
            await self.db.commit()
            raise InvalidRefreshTokenError()

        if stored.expires_at <= now:
            raise InvalidRefreshTokenError()

        user = await self.users.get_by_id(stored.user_id)
        if user is None or not user.is_active:
            raise InvalidRefreshTokenError()

        stored.revoked_at = now
        tokens = self._issue_tokens(user, now=now)

        await self.db.commit()
        return tokens

    async def logout(self, raw_token: str | None) -> None:
        if not raw_token:
            return
        stored = await self.tokens.get_by_hash(hash_refresh_token(raw_token))
        if stored is not None and stored.revoked_at is None:
            stored.revoked_at = datetime.now(UTC)
            await self.db.commit()

    def _issue_tokens(self, user: User, now: datetime | None = None) -> IssuedTokens:
        raw_refresh = generate_refresh_token()
        self.tokens.add(
            RefreshToken(
                user_id=user.id,
                token_hash=hash_refresh_token(raw_refresh),
                expires_at=refresh_token_expires_at(now),
            )
        )
        return IssuedTokens(
            access_token=create_access_token(user.id, now=now),
            refresh_token=raw_refresh,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
