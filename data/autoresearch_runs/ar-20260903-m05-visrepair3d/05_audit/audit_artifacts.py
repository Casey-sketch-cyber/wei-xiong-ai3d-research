from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


PRIMARY_METHODS = {
    "no_repair",
    "visibility_max_only",
    "random_feasible",
    "generic_greedy",
    "simulated_annealing",
    "revealrepair_attributed",
}
ABLATION_METHODS = {
    "ablation_visibility_only",
    "ablation_no_sparsity",
    "ablation_no_hard_filter",
    "ablation_targets_only",
    "ablation_partitions_only",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--pilot", type=Path)
    parser.add_argument("--full", type=Path)
    parser.add_argument("--analysis", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def finite_numeric_rows(rows: list[dict[str, str]], fields: list[str]) -> bool:
    try:
        return all(math.isfinite(float(row[field])) for row in rows for field in fields)
    except (KeyError, TypeError, ValueError):
        return False


def audit_pilot(path: Path) -> dict[str, Any]:
    rows = read_csv(path / "pilot_results.csv")
    with (path / "pilot_cases.json").open("r", encoding="utf-8") as handle:
        cases = json.load(handle)
    with (path / "pilot_summary.json").open("r", encoding="utf-8") as handle:
        summary = json.load(handle)
    counts = Counter(row["method"] for row in rows)
    pairs = [(row["case_id"], row["method"]) for row in rows]
    checks = {
        "case_count_15": len(cases) == 15 == summary["case_count"],
        "row_count_90": len(rows) == 90,
        "six_primary_methods": set(counts) == PRIMARY_METHODS,
        "balanced_method_counts": all(count == 15 for count in counts.values()),
        "unique_case_method_pairs": len(pairs) == len(set(pairs)),
        "numeric_values_finite": finite_numeric_rows(
            rows,
            [
                "schedule_loss",
                "missed_loss",
                "leakage_loss",
                "satisfaction",
                "edit_cost",
                "evaluations",
                "runtime_seconds",
            ],
        ),
        "reported_gate_passed": bool(summary["gate"]["overall_pass"]),
    }
    return {
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "method_counts": dict(sorted(counts.items())),
        "hashes": {
            name: sha256(path / name)
            for name in ("pilot_cases.json", "pilot_results.csv", "pilot_summary.json")
        },
    }


def audit_full(path: Path, analysis: Path | None, project: Path) -> dict[str, Any]:
    rows = read_csv(path / "full_results.csv")
    with (path / "frozen_config.json").open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    with (path / "run_metadata.json").open("r", encoding="utf-8") as handle:
        metadata = json.load(handle)
    with (path / "full_cases.json").open("r", encoding="utf-8") as handle:
        cases = json.load(handle)
    primary = [row for row in rows if row["method"] in PRIMARY_METHODS]
    ablations = [row for row in rows if row["method"] in ABLATION_METHODS]
    counts = Counter(row["method"] for row in primary)
    ablation_counts = Counter(row["method"] for row in ablations)
    pairs = [(row["case_id"], row["method"]) for row in rows]
    case_ids = {row["case_id"] for row in primary}
    result_hash = sha256(path / "full_results.csv")
    stride = int(config["ablation_stride"])
    severity_count = len(config["severity"])
    corruption_count = 5
    procedural_ablation_layouts = (
        math.ceil(int(config["procedural_layout_count"]) / stride) if stride > 0 else 0
    )
    llm_ablation_layouts = (
        math.ceil(int(config["llm_layout_count"]) / stride) if stride > 0 else 0
    )
    expected_ablation_cases = (
        (procedural_ablation_layouts + llm_ablation_layouts)
        * severity_count
        * corruption_count
    )
    expected_row_count = int(metadata["task_count"]) * len(PRIMARY_METHODS) + (
        expected_ablation_cases * len(ABLATION_METHODS)
    )
    protocol_payload = dict(config)
    recorded_protocol_hash = str(protocol_payload.pop("protocol_sha256"))
    core_paths = {
        "run_full.py": project / "04_full_experiment" / "run_full.py",
        "formal_benchmark.py": project / "04_full_experiment" / "formal_benchmark.py",
        "revealrepair_core.py": project / "03_pilot" / "revealrepair_core.py",
    }
    code_hashes_match = all(
        path_value.is_file()
        and sha256(path_value) == str(config["code_sha256"][name])
        for name, path_value in core_paths.items()
    )
    manifest_paths = {
        "procedural_manifest_sha256": project
        / "04_full_experiment"
        / "procedural_screen_v2"
        / "procedural_layout_manifest.json",
        "llm_manifest_sha256": project
        / "04_full_experiment"
        / "llm_layouts_qwen25_7b_v3_balanced"
        / "llm_layout_manifest.json",
    }
    input_manifest_hashes_match = all(
        manifest_path.is_file()
        and sha256(manifest_path) == str(config[config_key])
        for config_key, manifest_path in manifest_paths.items()
    )
    checks = {
        "run_completed": metadata["failed_or_missing"] == 0
        and metadata["succeeded"] == metadata["task_count"],
        "task_count_matches_cases": metadata["task_count"] == len(cases),
        "primary_rows_balanced": set(counts) == PRIMARY_METHODS
        and all(count == len(case_ids) for count in counts.values()),
        "unique_case_method_pairs": len(pairs) == len(set(pairs)),
        "frozen_task_count_matches": len(config["task_ids"]) == metadata["task_count"],
        "ablation_rows_balanced": set(ablation_counts) == ABLATION_METHODS
        and all(
            count == expected_ablation_cases for count in ablation_counts.values()
        ),
        "total_row_count_exact": len(rows) == expected_row_count,
        "frozen_protocol_hash_recomputes": (
            canonical_hash(protocol_payload) == recorded_protocol_hash
            and recorded_protocol_hash == metadata["protocol_sha256"]
        ),
        "frozen_core_code_hashes_match": code_hashes_match,
        "frozen_input_manifest_hashes_match": input_manifest_hashes_match,
        "numeric_values_finite": finite_numeric_rows(
            rows,
            [
                "schedule_loss",
                "missed_loss",
                "leakage_loss",
                "satisfaction",
                "edit_cost",
                "evaluations",
                "runtime_seconds",
            ],
        ),
    }
    analysis_hash_matches = None
    gate_passed = None
    if analysis is not None:
        with (analysis / "full_summary.json").open("r", encoding="utf-8") as handle:
            summary = json.load(handle)
        analysis_hash_matches = summary["input_sha256"] == sha256(path / "full_results.csv")
        gate_passed = bool(summary["gate"]["overall_pass"])
        checks["analysis_hash_matches_results"] = analysis_hash_matches
    derived_paths = {
        "failure_analysis": path / "failure_analysis" / "failure_summary.json",
        "robustness": path / "robustness" / "robustness_summary.json",
        "oracle": path / "oracle" / "oracle_summary.json",
        "stochastic_sensitivity": path
        / "stochastic_sensitivity"
        / "stochastic_sensitivity_summary.json",
    }
    derived_summaries = {}
    if all(summary_path.is_file() for summary_path in derived_paths.values()):
        checks["all_declared_derived_analyses_present"] = True
        for name, summary_path in derived_paths.items():
            with summary_path.open("r", encoding="utf-8") as handle:
                derived_summaries[name] = json.load(handle)
        checks["derived_source_hashes_match_results"] = all(
            summary["source_experiment_sha256"] == result_hash
            for summary in derived_summaries.values()
        )
        checks["robustness_gate_passed"] = bool(
            derived_summaries["robustness"]["gate"]["overall_pass"]
        )
    else:
        checks["all_declared_derived_analyses_present"] = False
    return {
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "reported_evidence_gate_passed": gate_passed,
        "primary_case_count": len(case_ids),
        "primary_method_counts": dict(sorted(counts.items())),
        "ablation_method_counts": dict(sorted(ablation_counts.items())),
        "expected_ablation_cases_per_method": expected_ablation_cases,
        "expected_total_row_count": expected_row_count,
        "derived_analysis_names": sorted(derived_summaries),
        "hashes": {
            name: sha256(path / name)
            for name in (
                "frozen_config.json",
                "full_cases.json",
                "full_results.csv",
                "run_metadata.json",
            )
        },
    }


def write_manifest(project: Path, path: Path) -> int:
    excluded_parts = {"__pycache__", ".git"}
    generated_outputs = {path.resolve(), (path.parent / "integrity_report.json").resolve()}
    entries = []
    for file_path in sorted(project.rglob("*")):
        if not file_path.is_file() or excluded_parts & set(file_path.parts):
            continue
        if file_path.resolve() in generated_outputs:
            continue
        entries.append(
            {
                "path": file_path.relative_to(project).as_posix(),
                "bytes": file_path.stat().st_size,
                "sha256": sha256(file_path),
            }
        )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "bytes", "sha256"])
        writer.writeheader()
        writer.writerows(entries)
    return len(entries)


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {}
    if args.pilot:
        report["pilot"] = audit_pilot(args.pilot)
    if args.full:
        report["full"] = audit_full(args.full, args.analysis, args.project)
    manifest_path = args.output / "sha256_manifest.csv"
    report["manifest_file_count"] = write_manifest(args.project, manifest_path)
    report["overall_integrity_pass"] = all(
        value["all_checks_pass"]
        for value in report.values()
        if isinstance(value, dict) and "all_checks_pass" in value
    )
    with (args.output / "integrity_report.json").open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
