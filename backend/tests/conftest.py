"""Shared test fixtures.

Test database
    `<POSTGRES_DB>_test` on the same server as the development database. Created
    automatically if missing.

Isolation
    Every test runs inside a transaction that is ROLLED BACK at the end.

Event loop
    One loop for the whole session
"""

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

import app.domains.auth.models
import app.domains.catalog.models
import app.domains.model_config.models
import app.domains.users.models
from app.core.config import settings
from app.core.database import Base, get_db
from app.domains.users.models import User
from app.domains.users.service import UserService
from app.main import app

TEST_DB_NAME = f"{settings.POSTGRES_DB}_test"
TEST_DB_URL = make_url(settings.DATABASE_URL).set(database=TEST_DB_NAME)

API = settings.API_V1_STR
USER_EMAIL = "john@test.com"
USER_PASSWORD = "test-password-123"


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------


async def _create_test_database_if_missing() -> None:
    admin = create_async_engine(
        make_url(settings.DATABASE_URL).set(database="postgres"), isolation_level="AUTOCOMMIT"
    )
    try:
        async with admin.connect() as conn:
            exists = await conn.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": TEST_DB_NAME}
            )
            if not exists:
                await conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
    finally:
        await admin.dispose()


@pytest.fixture(scope="session")
async def engine() -> AsyncIterator[AsyncEngine]:
    await _create_test_database_if_missing()
    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Session inside a transaction that is rolled back after the test."""
    async with engine.connect() as conn:
        transaction = await conn.begin()
        session = AsyncSession(
            bind=conn,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------


@pytest.fixture
async def client(db: AsyncSession) -> AsyncIterator[AsyncClient]:
    """Client that calls the app directly (no network), using the test session.

    Cookies persist between requests, like in a browser. https so that a cookie
    with the Secure flag (COOKIE_SECURE=true) is sent back as well.
    """

    async def _override_get_db() -> AsyncIterator[AsyncSession]:
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="https://test") as c:
            yield c
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


@pytest.fixture
async def user(db: AsyncSession) -> User:
    """Regular active user with USER_EMAIL / USER_PASSWORD."""
    return await UserService(db).create(email=USER_EMAIL, password=USER_PASSWORD)


@pytest.fixture
async def auth_headers(client: AsyncClient, user: User) -> dict[str, str]:
    """Authorization header of the logged-in `user`. The refresh cookie stays in `client`."""
    response = await client.post(
        f"{API}/auth/login", data={"username": user.email, "password": USER_PASSWORD}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
