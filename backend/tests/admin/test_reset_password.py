"""Admin command: a temporary password for a user who forgot theirs."""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.reset_password import reset_password, temporary_password
from tests.conftest import API, USER_EMAIL, USER_PASSWORD

TEMPORARY = "temporary-password-1"


async def login(client: AsyncClient, password: str) -> int:
    response = await client.post(
        f"{API}/auth/login", data={"username": USER_EMAIL, "password": password}
    )
    return response.status_code


async def test_the_temporary_password_replaces_the_old_one(
    client: AsyncClient, auth_headers: dict, db: AsyncSession
) -> None:
    assert await reset_password(db, USER_EMAIL, TEMPORARY)

    assert await login(client, USER_PASSWORD) == 401
    assert await login(client, TEMPORARY) == 200


async def test_reset_ends_every_session(
    client: AsyncClient, auth_headers: dict, db: AsyncSession
) -> None:
    await reset_password(db, USER_EMAIL, TEMPORARY)

    assert (await client.post(f"{API}/auth/refresh")).status_code == 401


async def test_email_is_matched_like_at_login(client: AsyncClient, user, db: AsyncSession) -> None:
    assert await reset_password(db, f"  {USER_EMAIL.upper()} ", TEMPORARY)
    assert await login(client, TEMPORARY) == 200


async def test_unknown_email_changes_nothing(db: AsyncSession) -> None:
    assert not await reset_password(db, "nobody@test.com", TEMPORARY)


def test_temporary_passwords_are_long_and_random() -> None:
    passwords = {temporary_password() for _ in range(100)}
    assert len(passwords) == 100
    assert all(len(p) >= 16 for p in passwords)
