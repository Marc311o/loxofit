"""Integration tests of the auth domain"""

from httpx import AsyncClient

from tests.conftest import API, USER_EMAIL, USER_PASSWORD

NEW_USER = {"email": "anna@test.com", "password": USER_PASSWORD}


async def test_register_creates_user(client: AsyncClient) -> None:
    response = await client.post(f"{API}/auth/register", json=NEW_USER)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == NEW_USER["email"]
    assert "password" not in body and "password_hash" not in body


async def test_each_test_starts_with_clean_database(client: AsyncClient) -> None:
    response = await client.post(f"{API}/auth/register", json=NEW_USER)
    assert response.status_code == 201


async def test_me_returns_logged_in_user(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    response = await client.get(f"{API}/auth/me", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["email"] == USER_EMAIL
