"""Engine CLI: plan file -> engine -> report, without a database."""

import json
from pathlib import Path

import pytest

from app.engine.types import MuscleTarget, Role
from app.scripts import engine_eval
from app.scripts.catalog_file import DATA_FILE, load_catalog
from app.scripts.config_versions import CONFIGS, DEFAULT_CONFIG_NAME, get_config
from app.scripts.engine_eval import PlanError, build_config, build_specs, build_targets, run, zone
from tests.engine.test_independence import imported_modules

EXAMPLE_PLAN = DATA_FILE.parent / "plans" / "example_upper_lower.json"
TARGET = MuscleTarget(mev=4, mav_upper=13, mrv=16)


def write_plan(tmp_path: Path, plan: dict) -> Path:
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan), encoding="utf-8")
    return path


def one_session(*exercises: tuple[str, int], max_minutes: int = 60, weeks: int = 3) -> dict:
    return {
        "weeks": weeks,
        "sessions": [
            {
                "name": "A",
                "max_minutes": max_minutes,
                "exercises": [{"exercise": e, "sets": s} for e, s in exercises],
            }
        ],
    }


# ---------------------------------------------------------------------------
# Adapter: catalog and config -> engine types
# ---------------------------------------------------------------------------


def test_specs_take_roles_and_flags_from_catalog():
    specs = build_specs(load_catalog())
    bench = specs["bb_bench"]
    assert bench.is_compound
    assert bench.muscle_roles["pec_major"] == Role.PRIMARY
    assert specs["leg_ext_uni"].is_unilateral


def test_default_config_maps_landmarks_and_role_weights():
    version = get_config(DEFAULT_CONFIG_NAME)
    config = build_config(version)
    targets = build_targets(version, load_catalog())

    assert config.weight(Role.SECONDARY) == 0.5
    assert targets["pec_major"] == TARGET
    assert "erectors" not in targets  # is_volume_target = FALSE in the catalog


def test_unknown_config_name_is_reported():
    with pytest.raises(KeyError, match="Unknown config"):
        get_config("no-such-config")


@pytest.mark.parametrize(
    ("volume", "expected"),
    [(3, "< MEV"), (4, "MEV-MAV"), (13, "MEV-MAV"), (15, "MAV-MRV"), (16.5, "> MRV")],
)
def test_zone_boundaries(volume, expected):
    assert zone(volume, TARGET) == expected


# ---------------------------------------------------------------------------
# Running a plan
# ---------------------------------------------------------------------------


def test_example_plan_runs_and_reports():
    result = run(EXAMPLE_PLAN)
    assert len(result.mesocycle.weeks) == 5
    assert result.mesocycle.weeks[-1].is_deload
    report = engine_eval.format_report(result)
    assert "SCORE" in report and "Muscles - week 1" in report


def test_weeks_option_overrides_the_file(tmp_path):
    result = run(write_plan(tmp_path, one_session(("bb_bench", 3), weeks=5)), weeks=3)
    assert len(result.mesocycle.weeks) == 3


def test_every_unknown_exercise_is_listed(tmp_path):
    path = write_plan(tmp_path, one_session(("no_such_one", 3), ("bb_bench", 3), ("nope", 2)))
    with pytest.raises(PlanError) as exc_info:
        run(path)
    assert len(exc_info.value.errors) == 2


def test_invalid_plan_structure_is_reported(tmp_path):
    path = write_plan(tmp_path, {"weeks": 1, "sessions": []})
    with pytest.raises(PlanError) as exc_info:
        run(path)
    assert len(exc_info.value.errors) == 2  # weeks < 2 and no sessions


def test_main_prints_json_and_returns_zero(capsys):
    assert engine_eval.main([str(EXAMPLE_PLAN), "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["config"] == DEFAULT_CONFIG_NAME
    assert data["score"] == pytest.approx(data["volume_score"] - data["time_penalty"])
    assert data["per_week"][-1]["is_deload"]


def test_main_returns_one_on_bad_plan(tmp_path, capsys):
    path = write_plan(tmp_path, one_session(("no_such_one", 3)))
    assert engine_eval.main([str(path)]) == 1
    assert "no_such_one" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# Standalone: the CLI and the modules it uses never touch the database
# ---------------------------------------------------------------------------

SCRIPTS_DIR = Path(engine_eval.__file__).parent


@pytest.mark.parametrize("name", ["catalog_file.py", "config_versions.py", "engine_eval.py"])
def test_cli_modules_do_not_import_database(name):
    modules = imported_modules(SCRIPTS_DIR / name)
    assert not any(m.startswith(("app.core", "sqlalchemy")) for m in modules)
    assert "app.domains.catalog.models" not in modules


def test_every_registered_config_is_supported_by_the_cli():
    catalog = load_catalog()
    for version in CONFIGS:
        build_config(version)
        build_targets(version, catalog)
