from __future__ import annotations

import argparse
import concurrent.futures
import csv
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any


PILOT_DIR = Path(__file__).resolve().parents[1] / "03_pilot"
if str(PILOT_DIR) not in sys.path:
    sys.path.insert(0, str(PILOT_DIR))

from revealrepair_core import (
    Action,
    Box,
    Scene,
    apply_action,
    edit_metrics,
    evaluate,
    standard_actions,
)
from formal_benchmark import FORMAL_ROTATION_DEGREES, FORMAL_TRANSLATION_STEPS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-cases", type=int, default=48)
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


def one_edit_oracle(task: dict[str, Any]) -> dict[str, Any]:
    initial = scene_from_dict(task["corrupted"])
    labels = {key: [int(value) for value in values] for key, values in task["labels"].items()}
    best_scene = initial
    best_eval = evaluate(initial, labels)
    best_key = (best_eval.schedule_loss, edit_metrics(initial, initial)[3])
    best_action: Action | None = None
    evaluations = 1
    actions = standard_actions(
        initial,
        [obj.object_id for obj in initial.objects if obj.movable],
        FORMAL_TRANSLATION_STEPS,
        FORMAL_ROTATION_DEGREES,
    )
    for action in actions:
        candidate = apply_action(initial, action)
        result = evaluate(candidate, labels)
        evaluations += 1
        if not result.hard_valid:
            continue
        key = (result.schedule_loss, edit_metrics(initial, candidate)[3])
        if key < best_key:
            best_scene = candidate
            best_eval = result
            best_key = key
            best_action = action
    return {
        "case_id": task["case_id"],
        "corruption": task["corruption"],
        "severity": int(task["severity"]),
        "oracle_schedule_loss": best_eval.schedule_loss,
        "oracle_edit_cost": edit_metrics(initial, best_scene)[3],
        "oracle_action": best_action.__dict__ if best_action else None,
        "oracle_evaluations": evaluations,
        "ours_schedule_loss": float(task["ours_schedule_loss"]),
        "ours_edit_cost": float(task["ours_edit_cost"]),
        "ours_edit_count": int(task["ours_edit_count"]),
        "ours_matches_oracle_loss": int(
            abs(float(task["ours_schedule_loss"]) - best_eval.schedule_loss) <= 1e-12
        ),
        "ours_matches_oracle_loss_and_cost": int(
            abs(float(task["ours_schedule_loss"]) - best_eval.schedule_loss) <= 1e-12
            and abs(float(task["ours_edit_cost"]) - edit_metrics(initial, best_scene)[3])
            <= 1e-9
        ),
    }


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.experiment / "full_cases.json").open("r", encoding="utf-8") as handle:
        cases = json.load(handle)
    with (args.experiment / "full_results.csv").open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    ours = {
        row["case_id"]: row
        for row in rows
        if row["method"] == "revealrepair_attributed"
    }
    eligible = [case for case in cases if case["corruption"] != "compound"]
    eligible.sort(
        key=lambda case: hashlib.sha256(case["case_id"].encode("utf-8")).hexdigest()
    )
    selected = eligible[: args.max_cases]
    tasks = [
        {
            "case_id": case["case_id"],
            "corruption": case["corruption"],
            "severity": case["severity"],
            "corrupted": case["corrupted"],
            "labels": case["labels"],
            "ours_schedule_loss": ours[case["case_id"]]["schedule_loss"],
            "ours_edit_cost": ours[case["case_id"]]["edit_cost"],
            "ours_edit_count": ours[case["case_id"]]["edit_count"],
        }
        for case in selected
    ]
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
        results = list(executor.map(one_edit_oracle, tasks))
    results.sort(key=lambda row: row["case_id"])
    with (args.output / "oracle_results.csv").open("w", encoding="utf-8", newline="") as handle:
        serializable = []
        for result in results:
            row = dict(result)
            row["oracle_action"] = json.dumps(
                row["oracle_action"], ensure_ascii=False, separators=(",", ":")
            )
            serializable.append(row)
        writer = csv.DictWriter(handle, fieldnames=list(serializable[0].keys()))
        writer.writeheader()
        writer.writerows(serializable)
    one_edit_ours = [row for row in results if row["ours_edit_count"] <= 1]
    summary = {
        "scope": "exact enumeration of no-op plus every single action in the shared formal action set",
        "selection": "non-compound cases sorted by SHA256(case_id), then first max-cases",
        "source_experiment_sha256": hashlib.sha256(
            (args.experiment / "full_results.csv").read_bytes()
        ).hexdigest(),
        "selected_case_ids_sha256": hashlib.sha256(
            json.dumps(
                [case["case_id"] for case in selected],
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest(),
        "selected_cases": len(results),
        "ours_one_edit_cases": len(one_edit_ours),
        "oracle_success_rate": sum(row["oracle_schedule_loss"] <= 0.005 for row in results)
        / len(results),
        "ours_matches_oracle_loss_rate_all": sum(
            row["ours_matches_oracle_loss"] for row in results
        )
        / len(results),
        "ours_matches_oracle_loss_rate_when_ours_one_edit": sum(
            row["ours_matches_oracle_loss"] for row in one_edit_ours
        )
        / max(len(one_edit_ours), 1),
        "ours_matches_oracle_loss_and_cost_rate_when_ours_one_edit": sum(
            row["ours_matches_oracle_loss_and_cost"] for row in one_edit_ours
        )
        / max(len(one_edit_ours), 1),
    }
    with (args.output / "oracle_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
