from __future__ import annotations

import argparse
import concurrent.futures
import csv
import hashlib
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np


PILOT_DIR = Path(__file__).resolve().parents[1] / "03_pilot"
if str(PILOT_DIR) not in sys.path:
    sys.path.insert(0, str(PILOT_DIR))

from revealrepair_core import Box, Scene, solve_annealing, solve_random
from formal_benchmark import FORMAL_ROTATION_DEGREES, FORMAL_TRANSLATION_STEPS


SEED_OFFSETS = [1013, 2027, 3041, 4051, 5059]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--per-stratum", type=int, default=1)
    parser.add_argument("--budget", type=int, default=480)
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    return parser.parse_args()


def scene_from_dict(value: dict[str, Any]) -> Scene:
    return Scene(
        scene_id=str(value["scene_id"]),
        room=[float(item) for item in value["room"]],
        route=[[float(item) for item in point] for point in value["route"]],
        objects=[Box(**item) for item in value["objects"]],
        exhibit_order=[str(item) for item in value["exhibit_order"]],
        protected_order=[str(item) for item in value["protected_order"]],
        surface_grid=int(value.get("surface_grid", 3)),
        path_check_step=float(value.get("path_check_step", 0.18)),
    )


def stable_key(case_id: str) -> str:
    return hashlib.sha256(case_id.encode("utf-8")).hexdigest()


def evaluate_task(task: dict[str, Any]) -> dict[str, Any]:
    scene = scene_from_dict(task["corrupted"])
    labels = {
        key: [int(value) for value in values]
        for key, values in task["labels"].items()
    }
    method = str(task["method"])
    if method == "random_feasible":
        result = solve_random(
            scene,
            labels,
            int(task["seed"]),
            int(task["budget"]),
            FORMAL_TRANSLATION_STEPS,
            FORMAL_ROTATION_DEGREES,
        )
    elif method == "simulated_annealing":
        result = solve_annealing(
            scene,
            labels,
            int(task["seed"]),
            int(task["budget"]),
            FORMAL_TRANSLATION_STEPS,
            FORMAL_ROTATION_DEGREES,
        )
    else:
        raise ValueError(f"unknown method: {method}")
    return {
        "case_id": task["case_id"],
        "source": task["source"],
        "corruption": task["corruption"],
        "severity": int(task["severity"]),
        "repeat": int(task["repeat"]),
        "seed": int(task["seed"]),
        "method": method,
        "schedule_loss": result.evaluation.schedule_loss,
        "success_at_0.005": int(result.evaluation.schedule_loss <= 0.005),
        "hard_valid": int(result.evaluation.hard_valid),
        "edit_count": result.edit_count,
        "edit_cost": result.edit_cost,
        "evaluations": result.evaluations,
        "runtime_seconds": result.runtime_seconds,
        "ours_schedule_loss": float(task["ours_schedule_loss"]),
        "ours_success_at_0.005": int(float(task["ours_schedule_loss"]) <= 0.005),
        "ours_nonworse": int(
            float(task["ours_schedule_loss"]) <= result.evaluation.schedule_loss + 1e-12
        ),
        "baseline_strictly_better": int(
            result.evaluation.schedule_loss + 1e-12 < float(task["ours_schedule_loss"])
        ),
    }


def main() -> None:
    args = parse_args()
    if not 1 <= args.repeats <= len(SEED_OFFSETS):
        raise ValueError(f"repeats must be between 1 and {len(SEED_OFFSETS)}")
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.experiment / "full_cases.json").open("r", encoding="utf-8") as handle:
        cases = json.load(handle)
    with (args.experiment / "full_results.csv").open(
        "r", encoding="utf-8", newline=""
    ) as handle:
        result_rows = list(csv.DictReader(handle))
    ours = {
        row["case_id"]: row
        for row in result_rows
        if row["method"] == "revealrepair_attributed"
    }

    strata: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        row = ours[case["case_id"]]
        strata[(row["source"], case["corruption"], int(case["severity"]))].append(case)
    selected: list[dict[str, Any]] = []
    for key in sorted(strata):
        candidates = sorted(strata[key], key=lambda case: stable_key(case["case_id"]))
        selected.extend(candidates[: args.per_stratum])

    tasks: list[dict[str, Any]] = []
    for case in selected:
        row = ours[case["case_id"]]
        for repeat, offset in enumerate(SEED_OFFSETS[: args.repeats], start=1):
            for method, method_offset in (
                ("random_feasible", 11),
                ("simulated_annealing", 29),
            ):
                tasks.append(
                    {
                        "case_id": case["case_id"],
                        "source": row["source"],
                        "corruption": case["corruption"],
                        "severity": case["severity"],
                        "corrupted": case["corrupted"],
                        "labels": case["labels"],
                        "method": method,
                        "repeat": repeat,
                        "seed": int(case["case_seed"]) + offset + method_offset,
                        "budget": args.budget,
                        "ours_schedule_loss": row["schedule_loss"],
                    }
                )

    rows: list[dict[str, Any]] = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
        for index, row in enumerate(executor.map(evaluate_task, tasks), start=1):
            rows.append(row)
            if index % 20 == 0 or index == len(tasks):
                print(f"completed {index}/{len(tasks)} sensitivity runs", flush=True)
    rows.sort(key=lambda row: (row["case_id"], row["method"], row["repeat"]))
    with (args.output / "stochastic_sensitivity_results.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    methods: dict[str, Any] = {}
    for method in ("random_feasible", "simulated_annealing"):
        subset = [row for row in rows if row["method"] == method]
        case_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in subset:
            case_groups[str(row["case_id"])].append(row)
        best_rows = [
            min(group, key=lambda row: float(row["schedule_loss"]))
            for group in case_groups.values()
        ]
        repeat_summaries = {}
        for repeat in range(1, args.repeats + 1):
            repeat_rows = [row for row in subset if row["repeat"] == repeat]
            repeat_summaries[str(repeat)] = {
                "n": len(repeat_rows),
                "success_rate_at_0.005": float(
                    np.mean([row["success_at_0.005"] for row in repeat_rows])
                ),
                "mean_schedule_loss": float(
                    np.mean([row["schedule_loss"] for row in repeat_rows])
                ),
                "ours_nonworse_rate": float(
                    np.mean([row["ours_nonworse"] for row in repeat_rows])
                ),
            }
        methods[method] = {
            "n_runs": len(subset),
            "success_rate_at_0.005": float(
                np.mean([row["success_at_0.005"] for row in subset])
            ),
            "median_schedule_loss": float(
                np.median([row["schedule_loss"] for row in subset])
            ),
            "hard_valid_rate": float(np.mean([row["hard_valid"] for row in subset])),
            "ours_nonworse_rate": float(np.mean([row["ours_nonworse"] for row in subset])),
            "baseline_strictly_better_rate": float(
                np.mean([row["baseline_strictly_better"] for row in subset])
            ),
            "best_of_repeats_success_rate_at_0.005": float(
                np.mean([row["success_at_0.005"] for row in best_rows])
            ),
            "best_of_repeats_median_schedule_loss": float(
                np.median([row["schedule_loss"] for row in best_rows])
            ),
            "ours_nonworse_rate_vs_best_of_repeats": float(
                np.mean(
                    [
                        float(row["ours_schedule_loss"])
                        <= float(row["schedule_loss"]) + 1e-12
                        for row in best_rows
                    ]
                )
            ),
            "best_of_repeats_strictly_better_than_ours_rate": float(
                np.mean(
                    [
                        float(row["schedule_loss"]) + 1e-12
                        < float(row["ours_schedule_loss"])
                        for row in best_rows
                    ]
                )
            ),
            "by_repeat": repeat_summaries,
        }

    selected_ours = [ours[case["case_id"]] for case in selected]
    summary = {
        "scope": "post-hoc stochastic-baseline sensitivity on a deterministic stratified subset",
        "selection": (
            f"first {args.per_stratum} SHA256-ranked case(s) per "
            "source x corruption x severity stratum"
        ),
        "selected_cases": len(selected),
        "strata": len(strata),
        "repeats": args.repeats,
        "seed_offsets": SEED_OFFSETS[: args.repeats],
        "budget_per_run": args.budget,
        "ours_fixed_success_rate": float(
            np.mean([float(row["schedule_loss"]) <= 0.005 for row in selected_ours])
        ),
        "methods": methods,
        "source_experiment_sha256": hashlib.sha256(
            (args.experiment / "full_results.csv").read_bytes()
        ).hexdigest(),
    }
    with (args.output / "stochastic_sensitivity_summary.json").open(
        "w", encoding="utf-8"
    ) as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
