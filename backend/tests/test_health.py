"""Tests of GET /health: database reachable -> 200, database down -> 503."""

import logging
from collections.abc import AsyncIterator

import pytest
from httpx import AsyncClient
from sqlalchemy.exc import OperationalError

from app.core.database import get_db
from app.main import app
from tests.conftest import API


class BrokenSession:
    """AsyncSession stand-in that fails like an unreachable database."""

    async def execute(self, *args, **kwargs):
        raise OperationalError("SELECT 1", {}, ConnectionRefusedError("connection refused"))


async def test_health_ok(client: AsyncClient) -> None:
    response = await client.get(f"{API}/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_health_returns_503_when_database_is_down(
    client: AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    async def _broken_db() -> AsyncIterator[BrokenSession]:
        yield BrokenSession()

    app.dependency_overrides[get_db] = _broken_db

    with caplog.at_level(logging.ERROR):
        response = await client.get(f"{API}/health")

    assert response.status_code == 503
    body = response.json()
    assert body["code"] == "SERVICE_UNAVAILABLE"
    assert set(body) == {"detail", "code"}
    assert any(r.exc_info and "SERVICE_UNAVAILABLE" in r.getMessage() for r in caplog.records)
