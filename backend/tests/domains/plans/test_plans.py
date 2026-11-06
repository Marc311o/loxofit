import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.model_config.models import ModelConfig
from app.domains.plans.models import PrescribedExercise
from app.domains.users.service import UserService
from tests.conftest import API
from tests.domains.conftest import Catalog

PLANS = f"{API}/plans"


@pytest.fixture
async def plan(client: AsyncClient, auth_headers: dict, default_config: ModelConfig) -> dict:
    response = await client.post(PLANS, json={"name": "Upper/Lower"}, headers=auth_headers)
    assert response.status_code == 201, response.text
    return response.json()


def _week(catalog: Catalog, *, sets: tuple[int, ...] = (3, 2)) -> dict:
    ids = [e.id for e in catalog.exercises.values()][: len(sets)]
    return {
        "sessions": [
            {
                "name": "Upper A",
                "exercises": [
                    {"exercise_id": i, "sets": s} for i, s in zip(ids, sets, strict=True)
                ],
            }
        ]
    }


async def test_new_plan_is_draft_with_empty_base_week(
    plan: dict, default_config: ModelConfig
) -> None:
    assert plan["status"] == "draft"
    assert [w["week_number"] for w in plan["weeks"]] == [1]
    assert plan["weeks"][0]["rir"] == default_config.rir_start
    assert plan["weeks"][0]["sessions"] == []


async def test_base_week_is_saved_in_order(
    client: AsyncClient, auth_headers: dict, plan: dict, catalog: Catalog
) -> None:
    response = await client.put(
        f"{PLANS}/{plan['id']}/base-week", json=_week(catalog), headers=auth_headers
    )
    assert response.status_code == 200, response.text
    session = response.json()["weeks"][0]["sessions"][0]
    assert session["position"] == 1
    assert [(e["slot"], e["sets"]) for e in session["exercises"]] == [(1, 3), (2, 2)]


async def test_removed_exercise_is_soft_deleted(
    client: AsyncClient, auth_headers: dict, plan: dict, catalog: Catalog, db: AsyncSession
) -> None:
    url = f"{PLANS}/{plan['id']}/base-week"
    saved = (await client.put(url, json=_week(catalog), headers=auth_headers)).json()
    session = saved["weeks"][0]["sessions"][0]
    kept = session["exercises"][0]

    body = {
        "sessions": [
            {
                "id": session["id"],
                "name": "Upper A",
                "exercises": [{"id": kept["id"], "exercise_id": kept["exercise_id"], "sets": 4}],
            }
        ]
    }
    response = await client.put(url, json=body, headers=auth_headers)

    assert response.status_code == 200, response.text
    exercises = response.json()["weeks"][0]["sessions"][0]["exercises"]
    assert [(e["id"], e["sets"]) for e in exercises] == [(kept["id"], 4)]
    rows = (await db.execute(select(PrescribedExercise))).scalars().all()
    assert len(rows) == 2
    assert sum(r.deleted_at is not None for r in rows) == 1


async def test_unknown_exercise_is_rejected(
    client: AsyncClient, auth_headers: dict, plan: dict, catalog: Catalog
) -> None:
    body = {"sessions": [{"name": "A", "exercises": [{"exercise_id": 999_999, "sets": 3}]}]}
    response = await client.put(f"{PLANS}/{plan['id']}/base-week", json=body, headers=auth_headers)
    assert response.status_code == 422
    assert response.json()["code"] == "INVALID_PLAN"


async def test_incomplete_plan_cannot_be_activated(
    client: AsyncClient, auth_headers: dict, plan: dict
) -> None:
    response = await client.post(f"{PLANS}/{plan['id']}/activate", headers=auth_headers)
    assert response.status_code == 409
    assert response.json()["code"] == "PLAN_INCOMPLETE"


async def test_no_active_plan(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.get(f"{PLANS}/active", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["code"] == "NO_ACTIVE_PLAN"


async def test_other_users_plan_is_not_found(
    client: AsyncClient, plan: dict, db: AsyncSession
) -> None:
    other = await UserService(db).create(email="eve@test.com", password="other-password-123")
    login = await client.post(
        f"{API}/auth/login", data={"username": other.email, "password": "other-password-123"}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = await client.get(f"{PLANS}/{plan['id']}", headers=headers)
    assert response.status_code == 404


async def test_delete_plan(client: AsyncClient, auth_headers: dict, plan: dict, catalog: Catalog):
    await client.put(f"{PLANS}/{plan['id']}/base-week", json=_week(catalog), headers=auth_headers)
    response = await client.delete(f"{PLANS}/{plan['id']}", headers=auth_headers)
    assert response.status_code == 204
    assert (await client.get(f"{PLANS}/{plan['id']}", headers=auth_headers)).status_code == 404
