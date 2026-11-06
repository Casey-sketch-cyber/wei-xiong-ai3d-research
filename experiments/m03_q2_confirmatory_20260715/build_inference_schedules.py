from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path


PRIMARY_SEED = 20260715
SECONDARY_SEED = 3407


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(4 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def include_input(row: dict[str, str]) -> bool:
    return not (row["split"] == "severity" and row["severity"] == "medium")


def job_id(row: dict[str, str]) -> str:
    return "--".join(
        [
            row["split"],
            row["view_id"],
            row["object_id"],
            row["style"],
            row["severity"],
        ]
    )


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with args.manifest.open("r", encoding="utf-8-sig", newline="") as handle:
        inputs = list(csv.DictReader(handle))
    selected = [row for row in inputs if include_input(row)]

    deterministic: list[dict[str, object]] = []
    stochastic: list[dict[str, object]] = []
    for row in selected:
        base = {"job_id": job_id(row), **row}
        deterministic.append({**base, "seed": ""})
        seeds = (
            (PRIMARY_SEED, SECONDARY_SEED)
            if row["split"] == "main"
            else (PRIMARY_SEED,)
        )
        for seed in seeds:
            stochastic.append({**base, "seed": seed})

    if len(deterministic) != 1020:
        raise RuntimeError(f"Expected 1020 deterministic jobs, found {len(deterministic)}")
    if len(stochastic) != 1740:
        raise RuntimeError(f"Expected 1740 stochastic jobs, found {len(stochastic)}")
    if len({row["job_id"] for row in deterministic}) != len(deterministic):
        raise RuntimeError("Deterministic job IDs are not unique")
    stochastic_ids = {(row["job_id"], row["seed"]) for row in stochastic}
    if len(stochastic_ids) != len(stochastic):
        raise RuntimeError("Stochastic job IDs are not unique")

    deterministic_path = args.output / "inference_schedule_deterministic.csv"
    stochastic_path = args.output / "inference_schedule_stochastic.csv"
    write_csv(deterministic_path, deterministic)
    write_csv(stochastic_path, stochastic)
    summary = {
        "input_manifest": str(args.manifest),
        "input_manifest_sha256": file_sha256(args.manifest),
        "deterministic_schedule": str(deterministic_path),
        "deterministic_sha256": file_sha256(deterministic_path),
        "deterministic_jobs": len(deterministic),
        "stochastic_schedule": str(stochastic_path),
        "stochastic_sha256": file_sha256(stochastic_path),
        "stochastic_jobs": len(stochastic),
        "primary_seed": PRIMARY_SEED,
        "secondary_seed": SECONDARY_SEED,
        "seed_policy": "both seeds for C120 main; primary seed for V30 and S30 low/high",
        "severity_medium_policy": "reuse corresponding C120 main outputs",
    }
    summary_path = args.output / "inference_schedule_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print("SCHEDULE_SUMMARY", json.dumps(summary, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
