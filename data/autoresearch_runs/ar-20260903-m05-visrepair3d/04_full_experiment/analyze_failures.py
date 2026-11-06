from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tolerance", type=float, default=0.005)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.experiment / "full_results.csv").open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    by_key = {(row["case_id"], row["method"]): row for row in rows}
    ours = [row for row in rows if row["method"] == "revealrepair_attributed"]
    failures = [row for row in ours if float(row["schedule_loss"]) > args.tolerance]
    records: list[dict[str, Any]] = []
    for row in failures:
        case_id = row["case_id"]
        no_repair = by_key[(case_id, "no_repair")]
        generic = by_key[(case_id, "generic_greedy")]
        annealing = by_key[(case_id, "simulated_annealing")]
        records.append(
            {
                "case_id": case_id,
                "source": row["source"],
                "corruption": row["corruption"],
                "severity": int(row["severity"]),
                "route_family": row["route_family"],
                "exhibit_count": int(row["exhibit_count"]),
                "initial_loss": float(no_repair["schedule_loss"]),
                "ours_loss": float(row["schedule_loss"]),
                "generic_loss": float(generic["schedule_loss"]),
                "annealing_loss": float(annealing["schedule_loss"]),
                "ours_edits": int(row["edit_count"]),
                "ours_evaluations": int(row["evaluations"]),
                "budget_exhausted": int(row["evaluations"]) >= 480,
                "ours_actions": row["actions"],
            }
        )
    records.sort(key=lambda value: value["ours_loss"], reverse=True)
    if records:
        with (args.output / "failure_cases.csv").open(
            "w", encoding="utf-8", newline=""
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=list(records[0].keys()))
            writer.writeheader()
            writer.writerows(records)
    summary = {
        "source_experiment_sha256": hashlib.sha256(
            (args.experiment / "full_results.csv").read_bytes()
        ).hexdigest(),
        "tolerance": args.tolerance,
        "total_cases": len(ours),
        "failure_count": len(failures),
        "failure_rate": len(failures) / max(len(ours), 1),
        "by_source": dict(Counter(row["source"] for row in failures)),
        "by_corruption": dict(Counter(row["corruption"] for row in failures)),
        "by_severity": dict(Counter(row["severity"] for row in failures)),
        "budget_exhaustion_rate_among_failures": (
            sum(record["budget_exhausted"] for record in records) / len(records)
            if records
            else 0.0
        ),
        "generic_better_on_failures": sum(
            record["generic_loss"] < record["ours_loss"] - 1e-12 for record in records
        ),
        "annealing_better_on_failures": sum(
            record["annealing_loss"] < record["ours_loss"] - 1e-12 for record in records
        ),
    }
    with (args.output / "failure_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
