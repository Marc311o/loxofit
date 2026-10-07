from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.core.database import db
from app.core.security import TokenError, decode_access_token
from app.domains.users.enums import UserRole
from app.domains.users.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Failed to authenticate user.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: db) -> type[User]:
    """Returns current user or 401"""
    try:
        user_id = decode_access_token(token)
    except TokenError as e:
        raise _unauthorized() from e

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise _unauthorized()

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def require_admin(user: CurrentUser) -> User:
    """Returns admin or 403 (or 401 by dependency if user not logged in)"""
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permission."
        )
    return user


AdminUser = Annotated[User, Depends(require_admin)]
