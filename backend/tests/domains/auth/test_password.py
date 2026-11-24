"""Changing the password: the session where it happens goes on, every other one ends."""

from httpx import AsyncClient

from app.core.config import settings
from tests.conftest import API, USER_EMAIL, USER_PASSWORD

NEW_PASSWORD = "brand-new-password-456"
COOKIE = settings.REFRESH_COOKIE_NAME


async def login(client: AsyncClient, password: str) -> int:
    response = await client.post(
        f"{API}/auth/login", data={"username": USER_EMAIL, "password": password}
    )
    return response.status_code


async def test_change_password_keeps_this_session_and_ends_the_others(
    client: AsyncClient, auth_headers: dict
) -> None:
    old_cookie = client.cookies[COOKIE]

    response = await client.post(
        f"{API}/auth/password",
        json={"current_password": USER_PASSWORD, "new_password": NEW_PASSWORD},
        headers=auth_headers,
    )

    assert response.status_code == 200
    new_access = response.json()["access_token"]
    new_cookie = client.cookies[COOKIE]
    assert new_cookie != old_cookie
    me = await client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {new_access}"})
    assert me.status_code == 200
    assert (await client.post(f"{API}/auth/refresh")).status_code == 200  # this session

    client.cookies.set(COOKIE, old_cookie, path=settings.REFRESH_COOKIE_PATH)
    assert (await client.post(f"{API}/auth/refresh")).status_code == 401  # the others


async def test_login_uses_the_new_password(client: AsyncClient, auth_headers: dict) -> None:
    await client.post(
        f"{API}/auth/password",
        json={"current_password": USER_PASSWORD, "new_password": NEW_PASSWORD},
        headers=auth_headers,
    )

    assert await login(client, USER_PASSWORD) == 401
    assert await login(client, NEW_PASSWORD) == 200


async def test_wrong_current_password_changes_nothing(
    client: AsyncClient, auth_headers: dict
) -> None:
    response = await client.post(
        f"{API}/auth/password",
        json={"current_password": "not-my-password", "new_password": NEW_PASSWORD},
        headers=auth_headers,
    )

    assert response.status_code == 403  # not 401 - the user stays logged in
    assert response.json()["code"] == "INCORRECT_PASSWORD"
    assert await login(client, USER_PASSWORD) == 200


async def test_new_password_too_short(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.post(
        f"{API}/auth/password",
        json={"current_password": USER_PASSWORD, "new_password": "short"},
        headers=auth_headers,
    )
    assert response.status_code == 422


async def test_change_password_requires_login(client: AsyncClient) -> None:
    response = await client.post(
        f"{API}/auth/password",
        json={"current_password": USER_PASSWORD, "new_password": NEW_PASSWORD},
    )
    assert response.status_code == 401
