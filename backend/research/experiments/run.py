"""
Runs the optimizers on the experiment scenarios and saves the results.

    python -m research.experiments.run compare            # TEST scenarios, 30 seeds
    python -m research.experiments.run tune               # TUNE scenarios x tuning grid, 10 seeds
    python -m research.experiments.run compare --seeds 5 --budget 5000 --workers 4
    python -m research.experiments.run compare --scenarios ul-4x60-gym,ppl-3x45-gym

Every run (scenario x algorithm variant x seed) is independent and seeded, so the
results do not depend on the number of workers or the order runs finish in.
Output, in research/experiments/results/<suite>/ unless --out says otherwise:

    runs.csv         one row per run: score, % of max, evaluations, time, plan size
    convergence.csv  best score so far at fixed checkpoints of every run
    plans.json       the best plan of every scenario x algorithm variant
    meta.json        everything needed to repeat the experiment
"""

import argparse
import csv
import json
import os
import platform
import random
import subprocess
import sys
import time
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from functools import cache
from multiprocessing import Pool
from pathlib import Path
from typing import Any

from app.domains.model_config.versions import DEFAULT_CONFIG_NAME, get_config
from app.engine.evaluate import evaluate_plan
from app.seeds.catalog_file import DATA_VERSION, load_catalog
from research.experiments.algorithms import REGISTRY, SUITES
from research.experiments.problem import Problem, build_problem
from research.experiments.scenarios import BY_NAME, Split, scenarios

RESULTS_DIR = Path(__file__).parent / "results"
CHECKPOINTS = 60  # convergence samples per run

SUITE_DEFAULTS: dict[str, dict[str, Any]] = {
    "compare": {"split": Split.TEST, "seeds": 30},
    "tune": {"split": Split.TUNE, "seeds": 10},
}

RUN_FIELDS = [
    "suite", "scenario", "family", "variant", "seed", "budget", "score", "max_score",
    "pct_of_max", "volume_score", "time_penalty", "overtime_min", "evaluations",
    "seconds", "exercises", "sets",
]  # fmt: skip
CONVERGENCE_FIELDS = ["suite", "scenario", "family", "variant", "seed", "evaluations", "best"]


@dataclass(frozen=True)
class Job:
    suite: str
    scenario: str
    algorithm: str  # REGISTRY key
    seed: int
    budget: int
    config: str


# -- one run (in a worker process) ------------------------------------------------------


@cache
def _problem(scenario: str, config: str) -> Problem:
    """Built once per worker process and scenario."""
    return build_problem(BY_NAME[scenario], load_catalog(), get_config(config))


def checkpoints(history: Sequence[tuple[int, float]], budget: int) -> list[tuple[int, float]]:
    """Best score so far at evenly spaced evaluation counts, from the improvement history.

    Before the first evaluation there is no score yet; after the last improvement the
    best one carries on (greedy may stop well before the budget).
    """
    points: list[tuple[int, float]] = []
    k, best = 0, None
    for step in range(1, CHECKPOINTS + 1):
        at = budget * step // CHECKPOINTS
        while k < len(history) and history[k][0] <= at:
            best = history[k][1]
            k += 1
        if best is not None:
            points.append((at, best))
    return points


def run_job(job: Job) -> dict[str, Any]:
    problem = _problem(job.scenario, job.config)
    algorithm = REGISTRY[job.algorithm]
    started = time.perf_counter()
    result = algorithm.run(problem.objective, problem.space, job.budget, random.Random(job.seed))
    seconds = time.perf_counter() - started

    objective = problem.objective
    sessions = objective.to_sessions(result.best)
    evaluation = evaluate_plan(sessions, objective.weeks, problem.targets, objective.config)
    row = {
        "suite": job.suite,
        "scenario": job.scenario,
        "family": algorithm.family,
        "variant": algorithm.variant,
        "seed": job.seed,
        "budget": job.budget,
        "score": result.score,
        "max_score": objective.max_score,
        "pct_of_max": 100 * result.score / objective.max_score,
        "volume_score": evaluation.volume_score,
        "time_penalty": evaluation.time_penalty,
        "overtime_min": sum(w.overtime_minutes for w in evaluation.weeks),
        "evaluations": result.evaluations,
        "seconds": seconds,
        "exercises": sum(len(s) for s in result.best),
        "sets": sum(sets for s in result.best for _, sets in s),
    }
    return {
        "row": row,
        "convergence": checkpoints(result.history, job.budget),
        "plan": problem.describe(result.best),
    }


# -- the whole suite ----------------------------------------------------------------------


def make_jobs(
    suite: str, scenario_names: Sequence[str], seeds: int, budget: int, config: str
) -> list[Job]:
    return [
        Job(suite, name, algorithm.key, seed, budget, config)
        for name in scenario_names
        for algorithm in SUITES[suite]
        for seed in range(seeds)
    ]


def _git_commit() -> str | None:
    try:
        command = ["git", "rev-parse", "HEAD"]
        out = subprocess.run(command, capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() or None


def run_suite(
    suite: str,
    scenario_names: Sequence[str],
    seeds: int,
    budget: int,
    workers: int,
    out: Path,
    config: str = DEFAULT_CONFIG_NAME,
) -> Path:
    jobs = make_jobs(suite, scenario_names, seeds, budget, config)
    out.mkdir(parents=True, exist_ok=True)
    meta = {
        "suite": suite,
        "started": datetime.now(UTC).isoformat(timespec="seconds"),
        "config": config,
        "catalog_data_version": DATA_VERSION,
        "budget": budget,
        "seeds": seeds,
        "scenarios": [asdict(BY_NAME[n]) for n in scenario_names],
        "algorithms": [
            {"family": a.family, "variant": a.variant, "params": a.params} for a in SUITES[suite]
        ],
        "workers": workers,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "git_commit": _git_commit(),
    }

    best_plans: dict[str, dict[str, Any]] = {}
    started = time.perf_counter()
    with (
        open(out / "runs.csv", "w", newline="", encoding="utf-8") as runs_file,
        open(out / "convergence.csv", "w", newline="", encoding="utf-8") as conv_file,
        Pool(workers) as pool,
    ):
        runs = csv.DictWriter(runs_file, RUN_FIELDS)
        conv = csv.writer(conv_file)
        runs.writeheader()
        conv.writerow(CONVERGENCE_FIELDS)
        step = max(1, len(jobs) // 50)
        for done, result in enumerate(pool.imap_unordered(run_job, jobs), start=1):
            row = result["row"]
            runs.writerow(row)
            ids = [row[k] for k in ("suite", "scenario", "family", "variant", "seed")]
            conv.writerows([*ids, at, best] for at, best in result["convergence"])

            key = f"{row['scenario']} | {row['family']}:{row['variant']}"
            if key not in best_plans or row["score"] > best_plans[key]["score"]:
                best_plans[key] = {"score": row["score"], "seed": row["seed"]}
                best_plans[key]["plan"] = result["plan"]

            if done % step == 0 or done == len(jobs):
                runs_file.flush()
                conv_file.flush()
                elapsed = time.perf_counter() - started
                eta = elapsed / done * (len(jobs) - done)
                print(f"[{done}/{len(jobs)}] {elapsed:6.0f} s, ~{eta:5.0f} s left", flush=True)

    meta["finished"] = datetime.now(UTC).isoformat(timespec="seconds")
    meta["seconds"] = round(time.perf_counter() - started, 1)
    (out / "plans.json").write_text(
        json.dumps(dict(sorted(best_plans.items())), indent=2), encoding="utf-8"
    )
    (out / "meta.json").write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")
    return out


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("suite", choices=sorted(SUITES))
    parser.add_argument("--seeds", type=int, help="runs per scenario and algorithm")
    parser.add_argument("--budget", type=int, default=30_000, help="evaluations per run")
    parser.add_argument("--workers", type=int, default=os.cpu_count() or 1)
    parser.add_argument("--scenarios", help="comma-separated names (default: the suite's split)")
    parser.add_argument("--config", default=DEFAULT_CONFIG_NAME, help="config version")
    parser.add_argument("--out", type=Path, help="output folder (default: results/<suite>)")
    args = parser.parse_args(argv)

    defaults = SUITE_DEFAULTS[args.suite]
    if args.scenarios:
        names = args.scenarios.split(",")
        if unknown := [n for n in names if n not in BY_NAME]:
            parser.error(f"unknown scenarios: {', '.join(unknown)}")
    else:
        names = [s.name for s in scenarios(defaults["split"])]

    seeds = args.seeds or defaults["seeds"]
    runs = len(names) * len(SUITES[args.suite]) * seeds
    print(f"{args.suite}: {len(names)} scenarios x {len(SUITES[args.suite])} algorithms "
          f"x {seeds} seeds = {runs} runs, {args.workers} workers")  # fmt: skip
    out = run_suite(
        args.suite, names, seeds, args.budget, args.workers,
        args.out or RESULTS_DIR / args.suite, args.config,
    )  # fmt: skip
    print(f"Results: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
