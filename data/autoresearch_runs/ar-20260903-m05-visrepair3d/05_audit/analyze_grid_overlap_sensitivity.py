from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


TOLERANCE = 0.005
PRIMARY_METHODS = {
    "no_repair",
    "visibility_max_only",
    "random_feasible",
    "generic_greedy",
    "simulated_annealing",
    "revealrepair_attributed",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(rows: list[dict[str, str]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for method in sorted(PRIMARY_METHODS):
        subset = [row for row in rows if row["method"] == method]
        losses = [float(row["schedule_loss"]) for row in subset]
        output[method] = {
            "n": len(subset),
            "mean_schedule_loss": sum(losses) / len(losses),
            "tolerance_satisfaction_rate": sum(
                loss <= TOLERANCE for loss in losses
            )
            / len(losses),
            "hard_valid_rate": sum(int(row["hard_valid"]) for row in subset)
            / len(subset),
        }
    return output


def main() -> None:
    args = parse_args()
    cases_path = args.experiment / "full_cases.json"
    results_path = args.experiment / "full_results.csv"
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    with results_path.open("r", encoding="utf-8", newline="") as handle:
        all_rows = list(csv.DictReader(handle))
    rows = [row for row in all_rows if row["method"] in PRIMARY_METHODS]
    overlap_ids = {
        str(case["case_id"])
        for case in cases
        if not bool(case["corruption_metadata"]["off_grid"])
    }
    overlap_rows = [row for row in rows if row["case_id"] in overlap_ids]
    excluded_rows = [row for row in rows if row["case_id"] not in overlap_ids]
    full_summary = summarize(rows)
    excluded_summary = summarize(excluded_rows)
    ours = "revealrepair_attributed"
    report = {
        "analysis_type": "post_hoc_partial_grid_overlap_exclusion_sensitivity",
        "reason": (
            "Eight compound severity-2 cases contain one on-grid subfault, "
            "although no complete known inverse is available in the search grid."
        ),
        "tolerance": TOLERANCE,
        "results_sha256": sha256(results_path),
        "cases_sha256": sha256(cases_path),
        "partial_overlap_case_count": len(overlap_ids),
        "partial_overlap_case_ids": sorted(overlap_ids),
        "partial_overlap_case_ids_sha256": hashlib.sha256(
            "\n".join(sorted(overlap_ids)).encode("utf-8")
        ).hexdigest(),
        "full_benchmark": full_summary,
        "excluding_partial_overlap_cases": excluded_summary,
        "partial_overlap_cases_only": summarize(overlap_rows),
        "revealrepair_change_after_exclusion": {
            "case_count": excluded_summary[ours]["n"] - full_summary[ours]["n"],
            "mean_schedule_loss": (
                excluded_summary[ours]["mean_schedule_loss"]
                - full_summary[ours]["mean_schedule_loss"]
            ),
            "tolerance_satisfaction_rate": (
                excluded_summary[ours]["tolerance_satisfaction_rate"]
                - full_summary[ours]["tolerance_satisfaction_rate"]
            ),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
