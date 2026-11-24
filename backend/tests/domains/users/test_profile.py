from httpx import AsyncClient

from tests.conftest import API
from tests.domains.conftest import Catalog

ME = f"{API}/users/me"
PROFILE = {"experience": "intermediate", "days_per_week": 4, "preferred_weekdays": [5, 1, 3, 4]}


async def test_profile_missing_until_set(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.get(f"{ME}/profile", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["code"] == "PROFILE_NOT_FOUND"


async def test_put_profile_creates_then_updates(client: AsyncClient, auth_headers: dict) -> None:
    created = await client.put(f"{ME}/profile", json=PROFILE, headers=auth_headers)
    updated = await client.put(
        f"{ME}/profile", json={**PROFILE, "max_session_minutes": 75}, headers=auth_headers
    )

    assert created.status_code == 200, created.text
    assert created.json()["preferred_weekdays"] == [1, 3, 4, 5]
    assert updated.json()["max_session_minutes"] == 75
    fetched = (await client.get(f"{ME}/profile", headers=auth_headers)).json()
    assert fetched["max_session_minutes"] == 75


async def test_duplicate_weekdays_rejected(client: AsyncClient, auth_headers: dict) -> None:
    body = {**PROFILE, "preferred_weekdays": [1, 1]}
    response = await client.put(f"{ME}/profile", json=body, headers=auth_headers)
    assert response.status_code == 422


async def test_set_and_replace_equipment(
    client: AsyncClient, auth_headers: dict, catalog: Catalog
) -> None:
    ids = [e.id for e in catalog.equipment.values()]

    first = await client.put(f"{ME}/equipment", json={"equipment_ids": ids}, headers=auth_headers)
    second = await client.put(
        f"{ME}/equipment", json={"equipment_ids": ids[:1]}, headers=auth_headers
    )

    assert first.status_code == 200, first.text
    assert {e["id"] for e in first.json()} == set(ids)
    assert [e["id"] for e in second.json()] == ids[:1]


async def test_unknown_equipment_rejected(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.put(
        f"{ME}/equipment", json={"equipment_ids": [999_999]}, headers=auth_headers
    )
    assert response.status_code == 422
    assert response.json()["code"] == "INVALID_EQUIPMENT"
