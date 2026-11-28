"""Workouts: start from the active plan, log sets, replace an exercise, finish or abandon."""

from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.adaptation.enums import AdjustmentReason
from app.domains.adaptation.models import LoadAdjustment
from app.domains.model_config.models import ModelConfig
from app.domains.users.models import User
from app.domains.users.service import UserService
from tests.conftest import API
from tests.domains.conftest import Catalog

PLANS = f"{API}/plans"
WORKOUTS = f"{API}/workouts"


@pytest.fixture
async def active_plan(
    client: AsyncClient, auth_headers: dict, catalog: Catalog, default_config: ModelConfig
) -> dict:
    """Upper A: bench press 3 sets (compound), cable fly 2 sets 12-15 reps (isolation)."""
    plan = (await client.post(PLANS, json={"name": "Plan"}, headers=auth_headers)).json()
    url = f"{PLANS}/{plan['id']}"
    week = {
        "sessions": [
            {
                "name": "Upper A",
                "exercises": [
                    {"exercise_id": catalog.exercises["bb_bench"].id, "sets": 3},
                    {
                        "exercise_id": catalog.exercises["cable_fly"].id,
                        "sets": 2,
                        "rep_min": 12,
                        "rep_max": 15,
                    },
                ],
            },
            {
                "name": "Upper B",
                "exercises": [{"exercise_id": catalog.exercises["lat_pulldown"].id, "sets": 3}],
            },
        ]
    }
    assert (await client.put(f"{url}/base-week", json=week, headers=auth_headers)).is_success
    assert (await client.post(f"{url}/progression", headers=auth_headers)).is_success
    response = await client.post(f"{url}/activate", headers=auth_headers)
    assert response.status_code == 200, response.text
    return response.json()


def session_id(plan: dict, week: int = 1, position: int = 1) -> str:
    return plan["weeks"][week - 1]["sessions"][position - 1]["id"]


async def start(client: AsyncClient, headers: dict, plan_session_id: str) -> dict:
    response = await client.post(
        WORKOUTS, json={"plan_session_id": plan_session_id}, headers=headers
    )
    assert response.status_code == 201, response.text
    return response.json()


def set_url(workout: dict, index: int = 0, number: int = 1) -> str:
    return f"{WORKOUTS}/{workout['id']}/exercises/{workout['exercises'][index]['id']}/sets/{number}"


async def log_set(client: AsyncClient, headers: dict, workout: dict, **body) -> dict:
    body = {"weight_kg": "60", "reps": 8, "rir": 2} | body
    response = await client.put(set_url(workout), json=body, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


# -- start --------------------------------------------------------------------


async def test_start_copies_the_targets_of_the_session(
    client: AsyncClient, auth_headers: dict, active_plan: dict, default_config: ModelConfig
) -> None:
    workout = await start(client, auth_headers, session_id(active_plan))

    assert workout["status"] == "in_progress"
    assert workout["session_name"] == "Upper A"
    assert workout["week_number"] == 1
    bench, fly = workout["exercises"]
    assert [bench["position"], fly["position"]] == [1, 2]
    assert (bench["target_sets"], bench["target_rep_min"], bench["target_rep_max"]) == (3, 6, 10)
    assert (fly["target_sets"], fly["target_rep_min"], fly["target_rep_max"]) == (2, 12, 15)
    assert bench["target_rir"] == fly["target_rir"] == default_config.rir_start
    assert bench["suggested_weight_kg"] is None
    assert bench["sets"] == []


async def test_rest_and_warm_up_follow_the_engine(
    client: AsyncClient, auth_headers: dict, active_plan: dict, default_config: ModelConfig
) -> None:
    bench, fly = (await start(client, auth_headers, session_id(active_plan)))["exercises"]
    assert (bench["rest_seconds"], bench["warm_up"]) == (default_config.rest_compound_s, True)
    assert (fly["rest_seconds"], fly["warm_up"]) == (default_config.rest_isolation_s, False)


async def test_start_suggests_the_newest_load(
    client: AsyncClient,
    auth_headers: dict,
    active_plan: dict,
    catalog: Catalog,
    user: User,
    db: AsyncSession,
) -> None:
    bench = catalog.exercises["bb_bench"].id
    for weight in ("60", "62.5"):
        db.add(
            LoadAdjustment(
                user_id=user.id,
                exercise_id=bench,
                weight_kg=Decimal(weight),
                reason=AdjustmentReason.PROGRESSED,
            )
        )
        await db.flush()

    workout = await start(client, auth_headers, session_id(active_plan))
    assert workout["exercises"][0]["suggested_weight_kg"] == "62.50"


async def test_start_copies_the_body_weight(
    client: AsyncClient, auth_headers: dict, active_plan: dict
) -> None:
    profile = {"experience": "beginner", "days_per_week": 3, "weight_kg": 81.5}
    assert (
        await client.put(f"{API}/users/me/profile", json=profile, headers=auth_headers)
    ).is_success

    workout = await start(client, auth_headers, session_id(active_plan))
    assert workout["body_weight_kg"] == "81.50"


async def test_one_workout_at_a_time(
    client: AsyncClient, auth_headers: dict, active_plan: dict
) -> None:
    await start(client, auth_headers, session_id(active_plan))
    response = await client.post(
        WORKOUTS,
        json={"plan_session_id": session_id(active_plan, position=2)},
        headers=auth_headers,
    )
    assert response.status_code == 409
    assert response.json()["code"] == "WORKOUT_IN_PROGRESS"


async def test_only_sessions_of_the_active_plan_can_be_started(
    client: AsyncClient, auth_headers: dict, active_plan: dict, catalog: Catalog
) -> None:
    draft = (await client.post(PLANS, json={"name": "Draft"}, headers=auth_headers)).json()
    week = {"sessions": [{"name": "X", "exercises": []}]}
    draft = (
        await client.put(f"{PLANS}/{draft['id']}/base-week", json=week, headers=auth_headers)
    ).json()

    response = await client.post(
        WORKOUTS, json={"plan_session_id": session_id(draft)}, headers=auth_headers
    )
    assert response.status_code == 404
    assert response.json()["code"] == "SESSION_NOT_FOUND"


async def test_sessions_can_be_done_in_any_order(
    client: AsyncClient, auth_headers: dict, active_plan: dict
) -> None:
    workout = await start(client, auth_headers, session_id(active_plan, week=2, position=2))
    assert (workout["week_number"], workout["session_name"]) == (2, "Upper B")


# -- current and history --------------------------------------------------------


async def test_current_workout(client: AsyncClient, auth_headers: dict, active_plan: dict) -> None:
    response = await client.get(f"{WORKOUTS}/current", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["code"] == "NO_WORKOUT_IN_PROGRESS"

    workout = await start(client, auth_headers, session_id(active_plan))
    response = await client.get(f"{WORKOUTS}/current", headers=auth_headers)
    assert response.json()["id"] == workout["id"]


async def test_history_lists_finished_workouts_only(
    client: AsyncClient, auth_headers: dict, active_plan: dict
) -> None:
    first = await start(client, auth_headers, session_id(active_plan))
    await log_set(client, auth_headers, first)
    await client.post(f"{WORKOUTS}/{first['id']}/finish", json={}, headers=auth_headers)
    second = await start(client, auth_headers, session_id(active_plan, position=2))
    await client.post(f"{WORKOUTS}/{second['id']}/abandon", headers=auth_headers)

    page = (await client.get(WORKOUTS, headers=auth_headers)).json()
    assert page["total"] == 1
    assert [w["id"] for w in page["items"]] == [first["id"]]


async def test_other_users_workout_is_not_found(
    client: AsyncClient, auth_headers: dict, active_plan: dict, db: AsyncSession
) -> None:
    workout = await start(client, auth_headers, session_id(active_plan))
    other = await UserService(db).create(email="eve@test.com", password="other-password-123")
    login = await client.post(
        f"{API}/auth/login", data={"username": other.email, "password": "other-password-123"}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    assert (await client.get(f"{WORKOUTS}/{workout['id']}", headers=headers)).status_code == 404
    response = await client.put(set_url(workout), json={"weight_kg": 1, "reps": 1}, headers=headers)
    assert response.status_code == 404


# -- sets -------------------------------------------------------------------------


async def test_saving_a_set_twice_keeps_one_set(
    client: AsyncClient, auth_headers: dict, active_plan: dict
) -> None:
    workout = await start(client, auth_headers, session_id(active_plan))
    await log_set(client, auth_headers, workout)
    result = await log_set(client, auth_headers, workout)

    sets = result["exercises"][0]["sets"]
    assert [(s["set_number"], s["weight_kg"], s["reps"], s["rir"]) for s in sets] == [
        (1, "60.00", 8, 2)
    ]


async def test_a_set_can_be_corrected(
    client: AsyncClient, auth_headers: dict, active_plan: dict
) -> None:
    workout = await start(client, auth_headers, session_id(active_plan))
    first = (await log_set(client, auth_headers, workout))["exercises"][0]["sets"][0]
    corrected = await log_set(client, auth_headers, workout, weight_kg="62.5", reps=7, rir=None)

    [s] = corrected["exercises"][0]["sets"]
    assert (s["weight_kg"], s["reps"], s["rir"]) == ("62.50", 7, None)
    assert s["completed_at"] == first["completed_at"]


async def test_a_set_can_be_deleted(
    client: AsyncClient, auth_headers: dict, active_plan: dict
) -> None:
    workout = await start(client, auth_headers, session_id(active_plan))
    await log_set(client, auth_headers, workout)

    response = await client.delete(set_url(workout), headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["exercises"][0]["sets"] == []

    response = await client.delete(set_url(workout), headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["code"] == "SET_NOT_FOUND"


@pytest.mark.parametrize(
    "body",
    [
        {"weight_kg": -1, "reps": 8},
        {"weight_kg": 60, "reps": 101},
        {"weight_kg": 60, "reps": 8, "rir": 6},
        {"weight_kg": "60.125", "reps": 8},
    ],
)
async def test_invalid_sets_are_rejected(
    client: AsyncClient, auth_headers: dict, active_plan: dict, body: dict
) -> None:
    workout = await start(client, auth_headers, session_id(active_plan))
    response = await client.put(set_url(workout), json=body, headers=auth_headers)
    assert response.status_code == 422


async def test_set_number_is_limited(
    client: AsyncClient, auth_headers: dict, active_plan: dict
) -> None:
    workout = await start(client, auth_headers, session_id(active_plan))
    body = {"weight_kg": 60, "reps": 8}
    response = await client.put(set_url(workout, number=11), json=body, headers=auth_headers)
    assert response.status_code == 422


# -- replacing an exercise ----------------------------------------------------------


async def test_exercise_is_replaced_in_the_workout_only(
    client: AsyncClient, auth_headers: dict, active_plan: dict, catalog: Catalog
) -> None:
    workout = await start(client, auth_headers, session_id(active_plan))
    fly = workout["exercises"][1]
    curl = catalog.exercises["cable_curl"].id

    response = await client.put(
        f"{WORKOUTS}/{workout['id']}/exercises/{fly['id']}/exercise",
        json={"exercise_id": curl},
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    replaced = response.json()["exercises"][1]
    assert replaced["exercise_id"] == curl
    assert (replaced["target_rep_min"], replaced["target_rep_max"]) == (12, 15)

    plan = (await client.get(f"{PLANS}/{active_plan['id']}", headers=auth_headers)).json()
    planned = plan["weeks"][0]["sessions"][0]["exercises"][1]
    assert planned["exercise_id"] == catalog.exercises["cable_fly"].id


async def test_default_rep_range_follows_the_new_exercise(
    client: AsyncClient, auth_headers: dict, active_plan: dict, catalog: Catalog
) -> None:
    workout = await start(client, auth_headers, session_id(active_plan))
    bench = workout["exercises"][0]
    response = await client.put(
        f"{WORKOUTS}/{workout['id']}/exercises/{bench['id']}/exercise",
        json={"exercise_id": catalog.exercises["cable_fly"].id},
        headers=auth_headers,
    )
    replaced = response.json()["exercises"][0]
    assert (replaced["target_rep_min"], replaced["target_rep_max"]) == (10, 14)


async def test_exercise_with_sets_cannot_be_replaced(
    client: AsyncClient, auth_headers: dict, active_plan: dict, catalog: Catalog
) -> None:
    workout = await start(client, auth_headers, session_id(active_plan))
    await log_set(client, auth_headers, workout)

    response = await client.put(
        f"{WORKOUTS}/{workout['id']}/exercises/{workout['exercises'][0]['id']}/exercise",
        json={"exercise_id": catalog.exercises["cable_curl"].id},
        headers=auth_headers,
    )
    assert response.status_code == 409
    assert response.json()["code"] == "EXERCISE_HAS_SETS"


async def test_unknown_exercise_cannot_replace(
    client: AsyncClient, auth_headers: dict, active_plan: dict
) -> None:
    workout = await start(client, auth_headers, session_id(active_plan))
    response = await client.put(
        f"{WORKOUTS}/{workout['id']}/exercises/{workout['exercises'][0]['id']}/exercise",
        json={"exercise_id": 999999},
        headers=auth_headers,
    )
    assert response.status_code == 404
    assert response.json()["code"] == "EXERCISE_NOT_FOUND"


# -- finishing and abandoning ---------------------------------------------------------


async def test_finished_workout_takes_its_session_off_the_queue(
    client: AsyncClient, auth_headers: dict, active_plan: dict
) -> None:
    workout = await start(client, auth_headers, session_id(active_plan))
    await log_set(client, auth_headers, workout)

    response = await client.post(
        f"{WORKOUTS}/{workout['id']}/finish",
        json={"session_rpe": 7, "notes": "Good"},
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    finished = response.json()
    assert finished["status"] == "finished"
    assert (finished["session_rpe"], finished["notes"]) == (7, "Good")
    assert finished["finished_at"] is not None

    response = await client.post(
        WORKOUTS, json={"plan_session_id": session_id(active_plan)}, headers=auth_headers
    )
    assert response.status_code == 409
    assert response.json()["code"] == "SESSION_ALREADY_DONE"


async def test_finished_workout_cannot_be_changed(
    client: AsyncClient, auth_headers: dict, active_plan: dict
) -> None:
    workout = await start(client, auth_headers, session_id(active_plan))
    await log_set(client, auth_headers, workout)
    await client.post(f"{WORKOUTS}/{workout['id']}/finish", json={}, headers=auth_headers)

    response = await client.put(
        set_url(workout), json={"weight_kg": 60, "reps": 8}, headers=auth_headers
    )
    assert response.status_code == 409
    assert response.json()["code"] == "WORKOUT_NOT_IN_PROGRESS"


async def test_empty_workout_cannot_be_finished(
    client: AsyncClient, auth_headers: dict, active_plan: dict
) -> None:
    workout = await start(client, auth_headers, session_id(active_plan))
    response = await client.post(
        f"{WORKOUTS}/{workout['id']}/finish", json={}, headers=auth_headers
    )
    assert response.status_code == 409
    assert response.json()["code"] == "WORKOUT_EMPTY"


@pytest.mark.parametrize("rpe", [0, 11])
async def test_session_rpe_is_between_1_and_10(
    client: AsyncClient, auth_headers: dict, active_plan: dict, rpe: int
) -> None:
    workout = await start(client, auth_headers, session_id(active_plan))
    await log_set(client, auth_headers, workout)
    response = await client.post(
        f"{WORKOUTS}/{workout['id']}/finish", json={"session_rpe": rpe}, headers=auth_headers
    )
    assert response.status_code == 422


async def test_abandoned_session_stays_in_the_queue(
    client: AsyncClient, auth_headers: dict, active_plan: dict
) -> None:
    workout = await start(client, auth_headers, session_id(active_plan))
    await log_set(client, auth_headers, workout)

    response = await client.post(f"{WORKOUTS}/{workout['id']}/abandon", headers=auth_headers)
    assert response.json()["status"] == "abandoned"

    again = await start(client, auth_headers, session_id(active_plan))
    assert again["id"] != workout["id"]


# -- the plan -------------------------------------------------------------------------


async def test_weeks_of_a_plan_with_workouts_are_locked(
    client: AsyncClient, auth_headers: dict, active_plan: dict, catalog: Catalog
) -> None:
    await start(client, auth_headers, session_id(active_plan))
    url = f"{PLANS}/{active_plan['id']}"
    week = {"sessions": [{"name": "X", "exercises": []}]}

    for response in (
        await client.put(f"{url}/base-week", json=week, headers=auth_headers),
        await client.post(f"{url}/progression", headers=auth_headers),
        await client.patch(url, json={"num_weeks": 4}, headers=auth_headers),
    ):
        assert response.status_code == 409
        assert response.json()["code"] == "PLAN_HAS_WORKOUTS"

    response = await client.patch(url, json={"name": "Renamed"}, headers=auth_headers)
    assert response.status_code == 200


async def test_workouts_outlive_their_plan(
    client: AsyncClient, auth_headers: dict, active_plan: dict
) -> None:
    workout = await start(client, auth_headers, session_id(active_plan))
    await log_set(client, auth_headers, workout)
    await client.post(f"{WORKOUTS}/{workout['id']}/finish", json={}, headers=auth_headers)
    await client.delete(f"{PLANS}/{active_plan['id']}", headers=auth_headers)

    response = await client.get(f"{WORKOUTS}/{workout['id']}", headers=auth_headers)
    assert response.status_code == 200
    kept = response.json()
    assert (kept["plan_session_id"], kept["week_number"]) == (None, None)
    assert kept["session_name"] == "Upper A"
    assert kept["exercises"][0]["rest_seconds"] is None
    assert len(kept["exercises"][0]["sets"]) == 1
