from __future__ import annotations

import argparse
import csv
import json
import platform
import sys
from pathlib import Path

import numpy as np

from revealrepair_core import (
    corrupt_scene,
    make_base_scene,
    no_repair,
    result_to_row,
    scene_to_dict,
    solve_annealing,
    solve_beam,
    solve_random,
)


CORRUPTIONS = [
    "premature_reveal",
    "missed_reveal",
    "back_facing",
    "target_displacement",
    "compound",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-seeds", type=int, default=3)
    parser.add_argument("--severity", type=int, nargs="+", default=[1])
    parser.add_argument("--budget", type=int, default=320)
    parser.add_argument("--beam-width", type=int, default=8)
    parser.add_argument("--max-depth", type=int, default=2)
    return parser.parse_args()


def summarize(rows: list[dict[str, object]]) -> dict[str, object]:
    methods = sorted({str(row["method"]) for row in rows})
    summary: dict[str, object] = {"case_count": len({row["case_id"] for row in rows})}
    method_rows: dict[str, object] = {}
    for method in methods:
        subset = [row for row in rows if row["method"] == method]
        method_rows[method] = {
            "n": len(subset),
            "mean_schedule_loss": float(np.mean([row["schedule_loss"] for row in subset])),
            "median_schedule_loss": float(np.median([row["schedule_loss"] for row in subset])),
            "mean_satisfaction": float(np.mean([row["satisfaction"] for row in subset])),
            "mean_missed_loss": float(np.mean([row["missed_loss"] for row in subset])),
            "mean_leakage_loss": float(np.mean([row["leakage_loss"] for row in subset])),
            "hard_valid_rate": float(np.mean([row["hard_valid"] for row in subset])),
            "median_edit_count": float(np.median([row["edit_count"] for row in subset])),
            "median_edit_cost": float(np.median([row["edit_cost"] for row in subset])),
            "mean_evaluations": float(np.mean([row["evaluations"] for row in subset])),
            "mean_runtime_seconds": float(np.mean([row["runtime_seconds"] for row in subset])),
        }
    summary["methods"] = method_rows

    no_rows = {str(row["case_id"]): row for row in rows if row["method"] == "no_repair"}
    ours = [row for row in rows if row["method"] == "revealrepair_attributed"]
    reductions = []
    both_components = []
    for row in ours:
        baseline = no_rows[str(row["case_id"])]
        denominator = max(float(baseline["schedule_loss"]), 1e-12)
        reductions.append((float(baseline["schedule_loss"]) - float(row["schedule_loss"])) / denominator)
        both_components.append(
            float(row["missed_loss"]) <= float(baseline["missed_loss"]) + 1e-12
            and float(row["leakage_loss"]) <= float(baseline["leakage_loss"]) + 1e-12
        )
    summary["gate"] = {
        "median_relative_loss_reduction": float(np.median(reductions)),
        "mean_relative_loss_reduction": float(np.mean(reductions)),
        "both_components_nonworse_rate": float(np.mean(both_components)),
        "all_hard_valid": all(int(row["hard_valid"]) == 1 for row in ours),
        "median_edit_count": float(np.median([row["edit_count"] for row in ours])),
        "pass_80pct_reduction": float(np.median(reductions)) >= 0.80,
        "pass_both_components": float(np.mean(both_components)) == 1.0,
        "pass_hard_constraints": all(int(row["hard_valid"]) == 1 for row in ours),
        "pass_sparse_edits": float(np.median([row["edit_count"] for row in ours])) <= 2.0,
    }
    solved_by_method: dict[str, list[dict[str, object]]] = {
        method: [
            row
            for row in rows
            if row["method"] == method and float(row["schedule_loss"]) <= 1e-12
        ]
        for method in methods
    }
    ours_solved = solved_by_method["revealrepair_attributed"]
    summary["gate"]["exact_solution_rate"] = len(ours_solved) / max(len(ours), 1)
    competitors = ["generic_greedy", "simulated_annealing", "random_feasible"]
    efficiency: dict[str, object] = {}
    paired_advantages: list[float] = []
    for competitor in competitors:
        competitor_by_case = {
            str(row["case_id"]): row for row in solved_by_method[competitor]
        }
        paired = [
            (float(competitor_by_case[str(row["case_id"])]["evaluations"]), float(row["evaluations"]))
            for row in ours_solved
            if str(row["case_id"]) in competitor_by_case
        ]
        efficiency[competitor] = {
            "paired_exact_cases": len(paired),
            "median_competitor_evaluations": float(np.median([item[0] for item in paired])) if paired else None,
            "median_ours_evaluations": float(np.median([item[1] for item in paired])) if paired else None,
            "median_evaluation_saving": float(np.median([item[0] - item[1] for item in paired])) if paired else None,
        }
        paired_advantages.extend(item[0] - item[1] for item in paired)
    summary["gate"]["efficiency_at_exact_solution"] = efficiency
    summary["gate"]["pass_search_efficiency"] = bool(paired_advantages) and float(
        np.median(paired_advantages)
    ) > 0.0
    summary["gate"]["overall_pass"] = all(
        summary["gate"][key]
        for key in (
            "pass_80pct_reduction",
            "pass_both_components",
            "pass_hard_constraints",
            "pass_sparse_edits",
            "pass_search_efficiency",
        )
    )
    return summary


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    cases: list[dict[str, object]] = []
    for base_seed in range(args.base_seeds):
        base, labels = make_base_scene(1000 + base_seed)
        for severity in args.severity:
            for corruption_index, corruption in enumerate(CORRUPTIONS):
                case_seed = 100_000 + base_seed * 1000 + severity * 100 + corruption_index
                corrupted, inverse = corrupt_scene(base, labels, corruption, severity, case_seed)
                case_id = corrupted.scene_id
                cases.append(
                    {
                        "case_id": case_id,
                        "base": scene_to_dict(base),
                        "corrupted": scene_to_dict(corrupted),
                        "labels": labels,
                        "known_inverse": [action.__dict__ for action in inverse],
                    }
                )
                print(f"case={case_id}", flush=True)
                results = [
                    no_repair(corrupted, labels),
                    solve_beam(
                        "visibility_max_only",
                        corrupted,
                        labels,
                        attributed=False,
                        objective="visibility_only",
                        max_depth=args.max_depth,
                        beam_width=args.beam_width,
                        max_evaluations=args.budget,
                    ),
                    solve_random(corrupted, labels, case_seed + 11, args.budget),
                    solve_beam(
                        "generic_greedy",
                        corrupted,
                        labels,
                        attributed=False,
                        max_depth=args.max_depth,
                        beam_width=args.beam_width,
                        max_evaluations=args.budget,
                    ),
                    solve_annealing(corrupted, labels, case_seed + 29, args.budget),
                    solve_beam(
                        "revealrepair_attributed",
                        corrupted,
                        labels,
                        attributed=True,
                        max_depth=args.max_depth,
                        beam_width=args.beam_width,
                        max_evaluations=args.budget,
                    ),
                ]
                for result in results:
                    row = result_to_row(case_id, corruption, severity, case_seed, result)
                    row["actions"] = json.dumps(row["actions"], separators=(",", ":"))
                    rows.append(row)
                    print(
                        f"  {result.method:25s} loss={result.evaluation.schedule_loss:.4f} "
                        f"sat={result.evaluation.satisfaction:.3f} edits={result.edit_count} "
                        f"valid={result.evaluation.hard_valid} evals={result.evaluations}",
                        flush=True,
                    )

    with (args.output / "pilot_cases.json").open("w", encoding="utf-8") as handle:
        json.dump(cases, handle, ensure_ascii=False, indent=2)
    with (args.output / "pilot_results.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    summary = summarize(rows)
    summary["environment"] = {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "arguments": vars(args) | {"output": str(args.output)},
    }
    with (args.output / "pilot_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
    print(json.dumps(summary["gate"], indent=2), flush=True)


if __name__ == "__main__":
    main()
