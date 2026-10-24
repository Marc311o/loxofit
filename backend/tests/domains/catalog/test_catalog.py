"""Integration tests of the catalog API on the hand-made catalog from conftest.py."""

import pytest
from httpx import AsyncClient

from tests.conftest import API
from tests.domains.catalog.conftest import Catalog

pytestmark = pytest.mark.usefixtures("catalog")


def codes(response) -> list[str]:
    body = response.json()
    items = body["items"] if isinstance(body, dict) else body
    return [item["code"] for item in items]


# ---------------------------------------------------------------------------
# Access
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", ["/muscles", "/equipment", "/exercises", "/exercises/1"])
async def test_catalog_requires_login(client: AsyncClient, path: str):
    response = await client.get(f"{API}{path}")
    assert response.status_code == 401
    assert response.json()["code"] == "NOT_AUTHENTICATED"


# ---------------------------------------------------------------------------
# Muscles and equipment
# ---------------------------------------------------------------------------


async def test_muscles_sorted_by_group_then_name(client, auth_headers):
    response = await client.get(f"{API}/muscles", headers=auth_headers)
    assert response.status_code == 200
    assert codes(response) == ["pec_major", "lats", "delt_ant", "biceps", "triceps"]


async def test_equipment_filter_by_category(client, auth_headers):
    response = await client.get(f"{API}/equipment?category=cable", headers=auth_headers)
    assert sorted(codes(response)) == ["cable_station", "lat_pulldown"]


async def test_equipment_search(client, auth_headers):
    response = await client.get(f"{API}/equipment?search=BENCH", headers=auth_headers)
    assert codes(response) == ["flat_bench"]


async def test_equipment_sorted_by_polish_name(client, auth_headers):
    response = await client.get(f"{API}/equipment?sort=name_pl", headers=auth_headers)
    # Polish collation: Ł sorts like L, before S and W (byte order would put it last)
    assert codes(response) == ["flat_bench", "barbell", "cable_station", "lat_pulldown"]


# ---------------------------------------------------------------------------
# Exercise list: pagination
# ---------------------------------------------------------------------------


async def test_exercise_page_metadata(client, auth_headers):
    response = await client.get(f"{API}/exercises?size=3", headers=auth_headers)
    body = response.json()
    assert (body["total"], body["page"], body["size"], body["pages"]) == (4, 1, 3, 2)
    assert len(body["items"]) == 3


async def test_pages_do_not_overlap(client, auth_headers):
    first = await client.get(f"{API}/exercises?size=2&page=1", headers=auth_headers)
    second = await client.get(f"{API}/exercises?size=2&page=2", headers=auth_headers)
    assert set(codes(first)).isdisjoint(codes(second))
    assert len(codes(first) + codes(second)) == 4


async def test_page_past_the_end_is_empty(client, auth_headers):
    body = (await client.get(f"{API}/exercises?size=2&page=5", headers=auth_headers)).json()
    assert body["items"] == [] and body["total"] == 4


@pytest.mark.parametrize("query", ["size=101", "size=0", "page=0", "unknown=1", "muscle_id=0"])
async def test_invalid_query_returns_422(client, auth_headers, query):
    response = await client.get(f"{API}/exercises?{query}", headers=auth_headers)
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# Exercise list: filters, search, sorting
# ---------------------------------------------------------------------------


async def test_filter_by_muscle_group(client, auth_headers):
    response = await client.get(f"{API}/exercises?muscle_group=chest", headers=auth_headers)
    assert sorted(codes(response)) == ["bb_bench", "cable_fly"]


async def test_filter_by_pattern(client, auth_headers):
    response = await client.get(f"{API}/exercises?pattern=vertical_pull", headers=auth_headers)
    assert codes(response) == ["lat_pulldown"]


async def test_filter_by_muscle_matches_any_role(client, auth_headers, catalog: Catalog):
    biceps = catalog.muscles["biceps"].id  # primary in curl, secondary in pull-down
    response = await client.get(f"{API}/exercises?muscle_id={biceps}", headers=auth_headers)
    assert sorted(codes(response)) == ["cable_curl", "lat_pulldown"]


async def test_filter_by_equipment(client, auth_headers, catalog: Catalog):
    cable = catalog.equipment["cable_station"].id
    response = await client.get(f"{API}/exercises?equipment_id={cable}", headers=auth_headers)
    assert sorted(codes(response)) == ["cable_curl", "cable_fly"]


async def test_filters_are_combined_with_and(client, auth_headers, catalog: Catalog):
    cable = catalog.equipment["cable_station"].id
    response = await client.get(
        f"{API}/exercises?muscle_group=chest&equipment_id={cable}", headers=auth_headers
    )
    assert codes(response) == ["cable_fly"]


@pytest.mark.parametrize(
    ("term", "expected"),
    [
        ("BENCH", ["bb_bench"]),  # case-insensitive, English name
        ("wyciąg", ["cable_curl", "cable_fly"]),  # Polish name, diacritics
        ("%", []),  # LIKE wildcards are matched literally
        ("_", []),
    ],
)
async def test_search(client, auth_headers, term, expected):
    response = await client.get(f"{API}/exercises", params={"search": term}, headers=auth_headers)
    assert sorted(codes(response)) == expected


@pytest.mark.parametrize(
    ("sort", "expected"),
    [
        ("name_en", ["bb_bench", "cable_curl", "cable_fly", "lat_pulldown"]),
        # Polish collation: Ś between R and U (byte order would put it last)
        ("name_pl", ["cable_fly", "lat_pulldown", "cable_curl", "bb_bench"]),
        # enum order chest, back, arms; then name_en
        ("group", ["bb_bench", "cable_fly", "lat_pulldown", "cable_curl"]),
    ],
)
async def test_sorting(client, auth_headers, sort, expected):
    response = await client.get(f"{API}/exercises?sort={sort}", headers=auth_headers)
    assert codes(response) == expected


async def test_list_item_includes_equipment(client, auth_headers):
    response = await client.get(f"{API}/exercises?search=bench", headers=auth_headers)
    (item,) = response.json()["items"]
    assert sorted(e["code"] for e in item["equipment"]) == ["barbell", "flat_bench"]


# ---------------------------------------------------------------------------
# Exercise detail
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("default_config")
async def test_detail_with_muscle_shares(client, auth_headers, catalog: Catalog):
    bench = catalog.exercises["bb_bench"].id
    response = await client.get(f"{API}/exercises/{bench}", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == "bb_bench"
    # 1.0 / 0.5 / 0.5 -> 50 / 25 / 25, largest first, ties by name_en
    assert [(m["muscle"]["code"], m["role"], m["share_pct"]) for m in body["muscles"]] == [
        ("pec_major", "primary", 50.0),
        ("delt_ant", "secondary", 25.0),
        ("triceps", "secondary", 25.0),
    ]


@pytest.mark.usefixtures("default_config")
async def test_detail_of_missing_exercise_returns_404(client, auth_headers):
    response = await client.get(f"{API}/exercises/999999", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["code"] == "EXERCISE_NOT_FOUND"


async def test_detail_with_invalid_id_returns_422(client, auth_headers):
    response = await client.get(f"{API}/exercises/0", headers=auth_headers)
    assert response.status_code == 422


async def test_detail_without_default_config_returns_500(client, auth_headers, catalog: Catalog):
    # No `default_config` fixture -> deployment error, reported with a stable code.
    bench = catalog.exercises["bb_bench"].id
    response = await client.get(f"{API}/exercises/{bench}", headers=auth_headers)
    assert response.status_code == 500
    assert response.json()["code"] == "DEFAULT_CONFIG_MISSING"
