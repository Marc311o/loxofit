import uuid
from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.database import get_db
from app.core.errors import register_exception_handlers
from app.core.security import create_access_token
from app.domains.auth.dependencies import AdminUser, CurrentUser
from app.domains.users.enums import UserRole
from app.domains.users.models import User


def make_user(role: UserRole = UserRole.USER, is_active: bool = True) -> User:
    return User(
        id=uuid.uuid4(),
        email=f"{uuid.uuid4().hex[:8]}@test.com",
        password_hash="irrelevant",
        role=role,
        is_active=is_active,
    )


class FakeSession:
    """AsyncSession stand-in - supports only get(), the only call the dependency makes."""

    def __init__(self, users: list[User]) -> None:
        self._users = {u.id: u for u in users}

    async def get(self, model, ident):
        return self._users.get(ident)


@pytest.fixture
def users() -> dict[str, User]:
    return {
        "user": make_user(),
        "admin": make_user(role=UserRole.ADMIN),
        "inactive": make_user(is_active=False),
    }


@pytest.fixture
async def client(users: dict[str, User]) -> AsyncIterator[AsyncClient]:
    app = FastAPI()
    register_exception_handlers(app)  # without it an AppError becomes a 500

    @app.get("/me")
    async def me(user: CurrentUser):
        return {"id": str(user.id)}

    @app.get("/admin")
    async def admin_only(user: AdminUser):
        return {"ok": True}

    app.dependency_overrides[get_db] = lambda: FakeSession(list(users.values()))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://test") as c:
        yield c


def auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


async def test_no_token_returns_401(client):
    assert (await client.get("/me")).status_code == 401


async def test_invalid_token_returns_401(client):
    response = await client.get("/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


async def test_valid_token_returns_user(client, users):
    response = await client.get("/me", headers=auth(users["user"]))
    assert response.status_code == 200
    assert response.json() == {"id": str(users["user"].id)}


async def test_token_of_unknown_user_returns_401(client):
    ghost = make_user()  # valid token, but the user is not in the "database"
    assert (await client.get("/me", headers=auth(ghost))).status_code == 401


async def test_inactive_user_returns_401(client, users):
    assert (await client.get("/me", headers=auth(users["inactive"]))).status_code == 401


async def test_admin_endpoint_forbidden_for_regular_user(client, users):
    assert (await client.get("/admin", headers=auth(users["user"]))).status_code == 403


async def test_admin_endpoint_allowed_for_admin(client, users):
    assert (await client.get("/admin", headers=auth(users["admin"]))).status_code == 200


async def test_admin_endpoint_without_token_returns_401(client):
    assert (await client.get("/admin")).status_code == 401
