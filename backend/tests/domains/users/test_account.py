"""Deleting the account: confirmed by the password, takes every piece of the user's data."""

from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.reset_password import reset_password
from app.core.config import settings
from app.domains.auth.models import RefreshToken
from app.domains.users.models import User, UserProfile
from tests.conftest import API, USER_EMAIL, USER_PASSWORD

PROFILE = {"experience": "beginner", "days_per_week": 3}


async def count(db: AsyncSession, model: type) -> int:
    return (await db.execute(select(func.count()).select_from(model))).scalar_one()


async def test_delete_account_removes_the_user_and_their_data(
    client: AsyncClient, auth_headers: dict, db: AsyncSession
) -> None:
    await client.put(f"{API}/users/me/profile", json=PROFILE, headers=auth_headers)

    response = await client.request(
        "DELETE", f"{API}/users/me", json={"password": USER_PASSWORD}, headers=auth_headers
    )

    assert response.status_code == 204
    assert settings.REFRESH_COOKIE_NAME not in client.cookies  # the cookie is cleared
    db.expire_all()
    assert await count(db, User) == 0
    assert await count(db, UserProfile) == 0
    assert await count(db, RefreshToken) == 0
    login = await client.post(
        f"{API}/auth/login", data={"username": USER_EMAIL, "password": USER_PASSWORD}
    )
    assert login.status_code == 401
    assert (await client.get(f"{API}/auth/me", headers=auth_headers)).status_code == 401


async def test_wrong_password_keeps_the_account(
    client: AsyncClient, auth_headers: dict, db: AsyncSession
) -> None:
    response = await client.request(
        "DELETE", f"{API}/users/me", json={"password": "not-my-password"}, headers=auth_headers
    )

    assert response.status_code == 403
    assert response.json()["code"] == "INCORRECT_PASSWORD"
    assert await count(db, User) == 1


async def test_admin_reset_password(client: AsyncClient, auth_headers: dict, db: AsyncSession):
    assert await reset_password(db, USER_EMAIL, "temporary-password-1")
    assert not await reset_password(db, "nobody@test.com", "temporary-password-1")

    old = await client.post(
        f"{API}/auth/login", data={"username": USER_EMAIL, "password": USER_PASSWORD}
    )
    new = await client.post(
        f"{API}/auth/login", data={"username": USER_EMAIL, "password": "temporary-password-1"}
    )
    assert (old.status_code, new.status_code) == (401, 200)
