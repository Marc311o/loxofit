"""Experiment runner: scenarios build, runs are reproducible, results are complete."""

import csv
import json

import pytest

from app.domains.model_config.versions import DEFAULT_CONFIG_NAME, get_config
from app.seeds.catalog_file import load_catalog
from research.experiments import run as runner
from research.experiments.algorithms import COMPARISON, REGISTRY, TUNING
from research.experiments.problem import available_exercises, build_problem
from research.experiments.scenarios import HOME, SCENARIOS, Split, scenarios


def test_tuning_and_test_scenarios_are_separate():
    tune, test = scenarios(Split.TUNE), scenarios(Split.TEST)
    assert tune and test
    assert not {s.name for s in tune} & {s.name for s in test}


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.name)
def test_every_scenario_builds(scenario):
    problem = build_problem(scenario, load_catalog(), get_config(DEFAULT_CONFIG_NAME))
    assert len(problem.space.pools) == scenario.sessions
    assert all(problem.space.pools)  # every session has something to choose from
    assert problem.objective.max_score > 0


def test_equipment_limits_the_catalog():
    catalog = load_catalog()
    home = set(available_exercises(catalog, HOME))
    assert "db_curl" in home and "bw_lunge_reverse" in home  # dumbbells; no equipment at all
    assert "bb_squat" not in home and "lat_pulldown_pron" not in home
    assert len(available_exercises(catalog, None)) == len(catalog.exercises)


def test_algorithm_keys_are_unique():
    keys = [a.key for a in COMPARISON + TUNING]
    assert len(set(keys)) == len(keys) == len(REGISTRY)


def test_checkpoints_carry_the_best_score_forward(monkeypatch):
    monkeypatch.setattr(runner, "CHECKPOINTS", 4)  # at 25, 50, 75 and 100 evaluations
    history = [(30, 1.0), (50, 2.0), (90, 3.0)]
    assert runner.checkpoints(history, 100) == [(50, 2.0), (75, 2.0), (100, 3.0)]


def test_suite_writes_complete_reproducible_results(tmp_path):
    def run(out):
        runner.run_suite("compare", ["fbw-3x45-home"], seeds=2, budget=300, workers=2, out=out)
        with open(out / "runs.csv", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        return {(r["family"], r["seed"]): r["score"] for r in rows}

    first = run(tmp_path / "a")
    assert len(first) == len(COMPARISON) * 2
    assert run(tmp_path / "b") == first  # same seeds - same results, whatever the timing

    meta = json.loads((tmp_path / "a" / "meta.json").read_text(encoding="utf-8"))
    assert meta["config"] == DEFAULT_CONFIG_NAME and meta["budget"] == 300
    plans = json.loads((tmp_path / "a" / "plans.json").read_text(encoding="utf-8"))
    assert len(plans) == len(COMPARISON)  # the best plan of every algorithm
    with open(tmp_path / "a" / "convergence.csv", encoding="utf-8") as f:
        assert sum(1 for _ in f) > len(first)  # several checkpoints per run
