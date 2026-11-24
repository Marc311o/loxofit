from datetime import timedelta

from fastapi import Response

from app.core.config import settings


def set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=token,
        max_age=int(timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS).total_seconds()),
        path=settings.REFRESH_COOKIE_PATH,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        path=settings.REFRESH_COOKIE_PATH,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
    )
