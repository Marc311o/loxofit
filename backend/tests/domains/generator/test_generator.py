"""Plan generator API: runs in the background, respects the equipment, saves as a plan.

The runner works in a thread on the test's session (the data of a test lives in its
uncommitted transaction); tests wait for it with `runner.join()`.
"""

from collections.abc import AsyncIterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.generator import runner as runner_module
from app.domains.generator.repository import GenerationRepository
from app.domains.generator.runner import GenerationRunner, get_runner, thin
from app.domains.generator.schemas import GenerationRequest
from app.domains.model_config.models import ModelConfig
from app.domains.users.models import User, UserEquipment
from app.domains.users.service import UserService
from app.main import app
from tests.conftest import API
from tests.domains.conftest import Catalog

RUNS = f"{API}/generator/runs"
FULL_BODY_2 = {"template": "full_body", "sessions": [{"weekday": 1}, {"weekday": 4}]}


@pytest.fixture
async def runner(db: AsyncSession) -> AsyncIterator[GenerationRunner]:
    @asynccontextmanager
    async def session() -> AsyncIterator[AsyncSession]:
        yield db

    with ThreadPoolExecutor(max_workers=1) as executor:
        runner = GenerationRunner(executor, {}, session)
        app.dependency_overrides[get_runner] = lambda: runner
        yield runner
        await runner.join()


async def _give_equipment(db: AsyncSession, user: User, catalog: Catalog, *codes: str) -> None:
    for code in codes or catalog.equipment:
        db.add(UserEquipment(user_id=user.id, equipment_id=catalog.equipment[code].id))
    await db.flush()


@pytest.fixture
async def equipped(db: AsyncSession, user: User, catalog: Catalog, default_config: ModelConfig):
    """The user owns all the equipment of the test catalog."""
    await _give_equipment(db, user, catalog)


async def _generate(client: AsyncClient, headers: dict, runner: GenerationRunner, body: dict):
    response = await client.post(RUNS, json=body, headers=headers)
    assert response.status_code == 202, response.text
    await runner.join()
    return (await client.get(f"{RUNS}/{response.json()['id']}", headers=headers)).json()


async def test_generates_a_plan_in_the_background(
    client: AsyncClient, auth_headers: dict, runner: GenerationRunner, equipped
) -> None:
    started = await client.post(RUNS, json=FULL_BODY_2, headers=auth_headers)
    assert started.status_code == 202, started.text
    body = started.json()
    assert body["status"] == "queued"
    assert body["progress"] == {"evaluations": 0, "budget": body["budget"], "best_score": None}

    await runner.join()
    run = (await client.get(f"{RUNS}/{body['id']}", headers=auth_headers)).json()

    assert run["status"] == "done", run["error"]
    assert run["progress"] is None
    assert run["evaluations"] == run["budget"]
    assert [s["name"] for s in run["sessions"]] == ["Full body A", "Full body B"]
    assert [s["weekday"] for s in run["sessions"]] == [1, 4]
    assert all(2 <= e["sets"] <= 5 for s in run["sessions"] for e in s["exercises"])
    scores = [score for _, score in run["history"]]
    assert scores == sorted(scores) and scores[-1] == run["score"]


async def test_only_exercises_the_user_has_equipment_for(
    client: AsyncClient,
    auth_headers: dict,
    runner: GenerationRunner,
    db: AsyncSession,
    user: User,
    catalog: Catalog,
    default_config: ModelConfig,
) -> None:
    await _give_equipment(db, user, catalog, "cable_station")
    run = await _generate(client, auth_headers, runner, FULL_BODY_2)

    used = {e["exercise_id"] for s in run["sessions"] for e in s["exercises"]}
    assert used <= {catalog.exercises["cable_fly"].id, catalog.exercises["cable_curl"].id}


async def test_session_nothing_fits_is_rejected_before_starting(
    client: AsyncClient,
    auth_headers: dict,
    runner: GenerationRunner,
    catalog: Catalog,
    default_config: ModelConfig,
) -> None:
    # No equipment at all - and the test catalog has no bodyweight exercises.
    response = await client.post(RUNS, json=FULL_BODY_2, headers=auth_headers)
    assert response.status_code == 422
    assert response.json()["code"] == "NO_EXERCISES_FOR_SESSION"


async def test_one_generation_at_a_time(
    client: AsyncClient, auth_headers: dict, runner: GenerationRunner, equipped
) -> None:
    first = await client.post(RUNS, json=FULL_BODY_2, headers=auth_headers)
    second = await client.post(RUNS, json=FULL_BODY_2, headers=auth_headers)
    assert first.status_code == 202
    assert second.status_code == 409
    assert second.json()["code"] == "GENERATION_IN_PROGRESS"

    await runner.join()
    third = await client.post(RUNS, json=FULL_BODY_2, headers=auth_headers)
    assert third.status_code == 202  # free again once the first one is done


async def test_same_seed_same_plan_new_seed_by_default(
    client: AsyncClient, auth_headers: dict, runner: GenerationRunner, equipped
) -> None:
    seeded = {**FULL_BODY_2, "seed": 7}
    first = await _generate(client, auth_headers, runner, seeded)
    second = await _generate(client, auth_headers, runner, seeded)
    assert first["seed"] == second["seed"] == 7
    assert first["sessions"] == second["sessions"]

    unseeded = await _generate(client, auth_headers, runner, FULL_BODY_2)
    assert unseeded["request"]["seed"] is None and unseeded["seed"] >= 0


async def test_upper_lower_needs_lower_body_exercises(
    client: AsyncClient, auth_headers: dict, runner: GenerationRunner, equipped
) -> None:
    body = {"template": "upper_lower", "sessions": [{}, {}]}
    response = await client.post(RUNS, json=body, headers=auth_headers)
    assert response.status_code == 422
    assert "session 2 (lower)" in response.json()["detail"]


async def test_custom_split_with_its_own_focuses(
    client: AsyncClient, auth_headers: dict, runner: GenerationRunner, catalog: Catalog, equipped
) -> None:
    body = {
        "template": "custom",
        "sessions": [{"focus": "push", "name": "Chest"}, {"focus": "pull"}],
    }
    run = await _generate(client, auth_headers, runner, body)

    assert [s["name"] for s in run["sessions"]] == ["Chest", "Pull"]
    push = {e["exercise_id"] for e in run["sessions"][0]["exercises"]}
    pull = {e["exercise_id"] for e in run["sessions"][1]["exercises"]}
    ex = catalog.exercises
    assert push <= {ex["bb_bench"].id, ex["cable_fly"].id}
    assert pull <= {ex["lat_pulldown"].id, ex["cable_curl"].id}


@pytest.mark.parametrize(
    "body",
    [
        {"template": "custom", "sessions": [{"focus": "push"}, {}]},  # custom needs every focus
        {"template": "full_body", "sessions": [{"focus": "push"}]},  # the template decides
        {"template": "full_body", "sessions": [{"weekday": 2}, {"weekday": 2}]},
        {"template": "full_body", "sessions": []},
    ],
)
async def test_invalid_requests(
    client: AsyncClient, auth_headers: dict, runner: GenerationRunner, body: dict
) -> None:
    response = await client.post(RUNS, json=body, headers=auth_headers)
    assert response.status_code == 422


async def test_unknown_muscle_priority_is_rejected(
    client: AsyncClient, auth_headers: dict, runner: GenerationRunner, equipped
) -> None:
    body = {**FULL_BODY_2, "targets": [{"muscle_id": 999_999, "priority": 2}]}
    response = await client.post(RUNS, json=body, headers=auth_headers)
    assert response.status_code == 422
    assert response.json()["code"] == "INVALID_GENERATION"


async def test_analysis_and_saving_as_a_plan(
    client: AsyncClient, auth_headers: dict, runner: GenerationRunner, catalog: Catalog, equipped
) -> None:
    lats = catalog.muscles["lats"].id
    body = {**FULL_BODY_2, "num_weeks": 4, "targets": [{"muscle_id": lats, "priority": 2}]}
    run = await _generate(client, auth_headers, runner, body)
    url = f"{RUNS}/{run['id']}"

    analysis = (await client.get(f"{url}/analysis", headers=auth_headers)).json()
    assert analysis["source"] == "projected"
    assert len(analysis["weeks"]) == 4
    assert analysis["score"] == pytest.approx(run["score"], abs=0.01)  # same plan, same score

    saved = await client.post(f"{url}/plan", json={"name": "Generated"}, headers=auth_headers)
    assert saved.status_code == 201, saved.text
    plan = saved.json()
    assert (plan["name"], plan["status"], plan["num_weeks"]) == ("Generated", "draft", 4)
    assert plan["config_id"] == run["config_id"]
    assert plan["muscle_targets"] == [{"muscle_id": lats, "priority": 2.0}]
    sessions = plan["weeks"][0]["sessions"]
    assert [s["name"] for s in sessions] == ["Full body A", "Full body B"]
    assert [[(e["exercise_id"], e["sets"]) for e in s["exercises"]] for s in sessions] == [
        [(e["exercise_id"], e["sets"]) for e in s["exercises"]] for s in run["sessions"]
    ]

    again = await client.post(f"{url}/plan", json={"name": "Twice"}, headers=auth_headers)
    assert again.status_code == 409
    assert again.json()["code"] == "GENERATION_ALREADY_SAVED"
    assert (await client.get(url, headers=auth_headers)).json()["plan_id"] == plan["id"]


async def test_unfinished_run_cannot_be_saved_or_analyzed(
    client: AsyncClient, auth_headers: dict, runner: GenerationRunner, equipped
) -> None:
    run = (await client.post(RUNS, json=FULL_BODY_2, headers=auth_headers)).json()
    url = f"{RUNS}/{run['id']}"
    # Not joined yet: the run is still queued.
    saved = await client.post(f"{url}/plan", json={"name": "Too early"}, headers=auth_headers)
    assert saved.status_code == 409 and saved.json()["code"] == "GENERATION_NOT_DONE"
    assert (await client.get(f"{url}/analysis", headers=auth_headers)).status_code == 409
    await runner.join()


async def test_failed_generation_is_reported(
    client: AsyncClient,
    auth_headers: dict,
    runner: GenerationRunner,
    equipped,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def broken(task, on_progress=None):
        raise RuntimeError("out of ideas")

    monkeypatch.setattr(runner_module, "generate", broken)
    run = await _generate(client, auth_headers, runner, FULL_BODY_2)
    assert (run["status"], run["error"], run["sessions"]) == ("failed", "out of ideas", None)


async def test_other_users_run_is_not_found(
    client: AsyncClient, auth_headers: dict, runner: GenerationRunner, db: AsyncSession, equipped
) -> None:
    run = await _generate(client, auth_headers, runner, FULL_BODY_2)
    other = await UserService(db).create(email="eve@test.com", password="other-password-123")
    login = await client.post(
        f"{API}/auth/login", data={"username": other.email, "password": "other-password-123"}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert (await client.get(f"{RUNS}/{run['id']}", headers=headers)).status_code == 404


async def test_interrupted_runs_are_failed_on_startup(
    client: AsyncClient, auth_headers: dict, runner: GenerationRunner, db: AsyncSession, equipped
) -> None:
    run = (await client.post(RUNS, json=FULL_BODY_2, headers=auth_headers)).json()
    await runner.join()
    await GenerationRepository(db).set(run["id"], status="running")  # as if the server died

    assert await GenerationRepository(db).fail_interrupted() == 1
    after = (await client.get(f"{RUNS}/{run['id']}", headers=auth_headers)).json()
    assert after["status"] == "failed" and "restart" in after["error"]


# -- pieces --------------------------------------------------------------------------------


def test_session_names_come_from_the_focus_with_letters_when_it_repeats():
    request = GenerationRequest.model_validate(
        {"template": "upper_lower", "sessions": [{}, {}, {"name": "Heavy upper"}, {}]}
    )
    assert request.session_names() == ["Upper A", "Lower A", "Heavy upper", "Lower B"]
    ppl = GenerationRequest.model_validate({"template": "push_pull_legs", "sessions": [{}] * 3})
    assert ppl.session_names() == ["Push", "Pull", "Lower"]


def test_history_is_thinned_keeping_both_ends():
    history = [(i, float(i)) for i in range(1000)]
    thinned = thin(history, limit=10)
    assert len(thinned) == 10
    assert thinned[0] == [0, 0.0] and thinned[-1] == [999, 999.0]
    assert thin(history[:5], limit=10) == [[i, float(i)] for i in range(5)]
