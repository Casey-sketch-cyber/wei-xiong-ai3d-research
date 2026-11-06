from __future__ import annotations

import argparse
import concurrent.futures
import csv
import hashlib
import json
import math
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np


PILOT_DIR = Path(__file__).resolve().parents[1] / "03_pilot"
if str(PILOT_DIR) not in sys.path:
    sys.path.insert(0, str(PILOT_DIR))

from revealrepair_core import Action, Box, Scene, apply_actions, evaluate


CONDITIONS = [
    "original",
    "surface_5x5",
    "route_2x",
    "surface_5x5_route_2x",
    "route_noise_5cm",
    "route_noise_10cm",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--subset-modulus", type=int, default=5)
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    parser.add_argument("--seed", type=int, default=20260904)
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


def nearest_resample_labels(labels: dict[str, list[int]], count: int) -> dict[str, list[int]]:
    old_count = len(next(iter(labels.values())))
    old_positions = np.linspace(0.0, 1.0, old_count)
    new_positions = np.linspace(0.0, 1.0, count)
    nearest = np.abs(old_positions[:, None] - new_positions[None, :]).argmin(axis=0)
    return {
        object_id: [int(values[index]) for index in nearest]
        for object_id, values in labels.items()
    }


def resample_route(scene: Scene, count: int) -> Scene:
    result = scene.clone()
    route = np.asarray(scene.route, dtype=float)
    old_positions = np.linspace(0.0, 1.0, len(route))
    new_positions = np.linspace(0.0, 1.0, count)
    result.route = [
        [float(np.interp(value, old_positions, route[:, axis])) for axis in range(3)]
        for value in new_positions
    ]
    return result


def perturb_route(scene: Scene, sigma: float, seed: int) -> Scene:
    result = scene.clone()
    rng = np.random.default_rng(seed)
    noise = rng.normal(0.0, sigma, size=(len(result.route), 2))
    noise[0] = 0.0
    noise[-1] = 0.0
    for index, point in enumerate(result.route):
        point[0] += float(noise[index, 0])
        point[1] += float(noise[index, 1])
    return result


def evaluate_condition(task: dict[str, Any]) -> dict[str, Any]:
    corrupted = scene_from_dict(task["corrupted"])
    actions = [Action(**value) for value in task["actions"]]
    repaired = apply_actions(corrupted, actions)
    labels = {key: [int(value) for value in values] for key, values in task["labels"].items()}
    condition = str(task["condition"])
    if condition in {"route_2x", "surface_5x5_route_2x"}:
        repaired = resample_route(repaired, len(repaired.route) * 2 - 1)
        corrupted = resample_route(corrupted, len(corrupted.route) * 2 - 1)
        labels = nearest_resample_labels(labels, len(repaired.route))
    if condition in {"surface_5x5", "surface_5x5_route_2x"}:
        repaired.surface_grid = 5
        corrupted.surface_grid = 5
    if condition == "route_noise_5cm":
        repaired = perturb_route(repaired, 0.05, int(task["noise_seed"]))
        corrupted = perturb_route(corrupted, 0.05, int(task["noise_seed"]))
    if condition == "route_noise_10cm":
        repaired = perturb_route(repaired, 0.10, int(task["noise_seed"]))
        corrupted = perturb_route(corrupted, 0.10, int(task["noise_seed"]))
    before = evaluate(corrupted, labels)
    after = evaluate(repaired, labels)
    return {
        "case_id": task["case_id"],
        "source": task["source"],
        "corruption": task["corruption"],
        "severity": int(task["severity"]),
        "condition": condition,
        "before_schedule_loss": before.schedule_loss,
        "after_schedule_loss": after.schedule_loss,
        "relative_loss_reduction": (
            (before.schedule_loss - after.schedule_loss) / max(before.schedule_loss, 1e-12)
        ),
        "success_at_0.005": int(after.schedule_loss <= 0.005),
        "hard_valid": int(after.hard_valid),
        "missed_loss": after.missed_loss,
        "leakage_loss": after.leakage_loss,
    }


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.experiment / "full_cases.json").open("r", encoding="utf-8") as handle:
        cases = json.load(handle)
    with (args.experiment / "full_results.csv").open("r", encoding="utf-8", newline="") as handle:
        result_rows = list(csv.DictReader(handle))
    ours = {
        row["case_id"]: row
        for row in result_rows
        if row["method"] == "revealrepair_attributed"
    }
    selected = [
        case
        for case in cases
        if int(hashlib.sha256(case["case_id"].encode("utf-8")).hexdigest(), 16)
        % args.subset_modulus
        == 0
    ]
    tasks = []
    for case_index, case in enumerate(selected):
        row = ours[case["case_id"]]
        actions = json.loads(row["actions"])
        for condition_index, condition in enumerate(CONDITIONS):
            tasks.append(
                {
                    "case_id": case["case_id"],
                    "source": row["source"],
                    "corruption": case["corruption"],
                    "severity": case["severity"],
                    "corrupted": case["corrupted"],
                    "labels": case["labels"],
                    "actions": actions,
                    "condition": condition,
                    "noise_seed": args.seed + case_index * 10 + condition_index,
                }
            )
    rows: list[dict[str, Any]] = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
        for index, row in enumerate(executor.map(evaluate_condition, tasks), start=1):
            rows.append(row)
            if index % 25 == 0 or index == len(tasks):
                print(f"completed {index}/{len(tasks)} robustness evaluations", flush=True)
    rows.sort(key=lambda row: (row["case_id"], row["condition"]))
    with (args.output / "robustness_results.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    conditions: dict[str, Any] = {}
    for condition in CONDITIONS:
        subset = [row for row in rows if row["condition"] == condition]
        conditions[condition] = {
            "n": len(subset),
            "success_rate_at_0.005": float(
                np.mean([row["success_at_0.005"] for row in subset])
            ),
            "hard_valid_rate": float(np.mean([row["hard_valid"] for row in subset])),
            "mean_after_loss": float(np.mean([row["after_schedule_loss"] for row in subset])),
            "median_relative_loss_reduction": float(
                np.median([row["relative_loss_reduction"] for row in subset])
            ),
        }
    summary = {
        "source_experiment_sha256": hashlib.sha256(
            (args.experiment / "full_results.csv").read_bytes()
        ).hexdigest(),
        "subset_rule": f"sha256(case_id) mod {args.subset_modulus} == 0",
        "selected_cases": len(selected),
        "evaluation_count": len(rows),
        "conditions": conditions,
        "gate": {
            "dense_both_success_at_least_0.75": conditions[
                "surface_5x5_route_2x"
            ]["success_rate_at_0.005"]
            >= 0.75,
            "noise_10cm_success_at_least_0.70": conditions[
                "route_noise_10cm"
            ]["success_rate_at_0.005"]
            >= 0.70,
            "all_conditions_hard_valid": all(
                value["hard_valid_rate"] == 1.0 for value in conditions.values()
            ),
        },
    }
    summary["gate"]["overall_pass"] = all(summary["gate"].values())
    with (args.output / "robustness_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
