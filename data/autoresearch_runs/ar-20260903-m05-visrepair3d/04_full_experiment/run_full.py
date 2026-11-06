from __future__ import annotations

import argparse
import concurrent.futures
import csv
import hashlib
import json
import os
import platform
import sys
import time
import traceback
from pathlib import Path
from typing import Any


os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

from formal_benchmark import CORRUPTIONS, run_case


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed-start", type=int, default=3000)
    parser.add_argument("--base-seeds", type=int, default=20)
    parser.add_argument("--severity", type=int, nargs="+", default=[1, 2, 3])
    parser.add_argument("--budget", type=int, default=480)
    parser.add_argument("--beam-width", type=int, default=8)
    parser.add_argument("--max-depth", type=int, default=3)
    parser.add_argument("--route-samples", type=int, default=36)
    parser.add_argument("--surface-grid", type=int, default=3)
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    parser.add_argument("--ablation-stride", type=int, default=5)
    parser.add_argument("--procedural-manifest", type=Path)
    parser.add_argument("--llm-manifest", type=Path)
    parser.add_argument("--max-tasks", type=int)
    return parser.parse_args()


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_llm_manifest(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    layouts = payload.get("accepted_layouts", payload) if isinstance(payload, dict) else payload
    if not isinstance(layouts, list):
        raise ValueError("LLM manifest must contain a list of layout specifications")
    return [dict(item) for item in layouts]


def build_tasks(args: argparse.Namespace) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    if args.procedural_manifest:
        with args.procedural_manifest.open("r", encoding="utf-8") as handle:
            procedural_payload = json.load(handle)
        procedural_layouts = procedural_payload["accepted_layouts"]
    else:
        procedural_layouts = [
            {
                "seed": args.seed_start + index,
                "case_seed_base": 700_000 + index * 1000,
            }
            for index in range(args.base_seeds)
        ]
    for base_index, layout in enumerate(procedural_layouts):
        base_seed = int(layout["seed"])
        case_seed_base = int(layout.get("case_seed_base", 700_000 + base_index * 1000))
        for severity in args.severity:
            for corruption_index, corruption in enumerate(CORRUPTIONS):
                task_id = f"proc_{base_seed}_{corruption}_s{severity}"
                tasks.append(
                    {
                        "task_id": task_id,
                        "source": "procedural",
                        "base_seed": base_seed,
                        "severity": severity,
                        "corruption": corruption,
                        "case_seed": case_seed_base + severity * 100 + corruption_index,
                        "budget": args.budget,
                        "beam_width": args.beam_width,
                        "max_depth": args.max_depth,
                        "route_samples": args.route_samples,
                        "surface_grid": args.surface_grid,
                        "run_ablations": args.ablation_stride > 0
                        and base_index % args.ablation_stride == 0,
                    }
                )

    llm_layouts = load_llm_manifest(args.llm_manifest)
    for layout_index, layout in enumerate(llm_layouts):
        base_seed = int(layout.get("seed", 9000 + layout_index))
        layout_id = str(layout.get("layout_id", f"llm_{layout_index:03d}"))
        layout["layout_id"] = layout_id
        layout["source"] = "llm"
        for severity in args.severity:
            for corruption_index, corruption in enumerate(CORRUPTIONS):
                task_id = f"llm_{layout_id}_{corruption}_s{severity}"
                tasks.append(
                    {
                        "task_id": task_id,
                        "source": "llm",
                        "overrides": layout,
                        "base_seed": base_seed,
                        "severity": severity,
                        "corruption": corruption,
                        "case_seed": 1_700_000
                        + layout_index * 1000
                        + severity * 100
                        + corruption_index,
                        "budget": args.budget,
                        "beam_width": args.beam_width,
                        "max_depth": args.max_depth,
                        "route_samples": args.route_samples,
                        "surface_grid": args.surface_grid,
                        "run_ablations": args.ablation_stride > 0
                        and layout_index % args.ablation_stride == 0,
                    }
                )
    tasks.sort(key=lambda item: str(item["task_id"]))
    if args.max_tasks is not None:
        tasks = tasks[: args.max_tasks]
    return tasks


def load_completed(path: Path) -> dict[str, dict[str, Any]]:
    completed: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return completed
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            completed[str(record["task_id"])] = record
    return completed


def append_jsonl(path: Path, value: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def write_outputs(
    output: Path,
    task_ids: set[str],
    completed: dict[str, dict[str, Any]],
) -> None:
    selected = [completed[task_id] for task_id in sorted(task_ids) if task_id in completed]
    cases = [record["case"] for record in selected]
    rows: list[dict[str, Any]] = []
    for record in selected:
        for raw_row in record["rows"]:
            row = dict(raw_row)
            if not isinstance(row.get("actions"), str):
                row["actions"] = json.dumps(
                    row.get("actions", []), ensure_ascii=False, separators=(",", ":")
                )
            rows.append(row)
    with (output / "full_cases.json").open("w", encoding="utf-8") as handle:
        json.dump(cases, handle, ensure_ascii=False, separators=(",", ":"))
    if rows:
        fields = list(rows[0].keys())
        with (output / "full_results.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    tasks = build_tasks(args)
    task_ids = {str(task["task_id"]) for task in tasks}
    frozen_config = {
        "seed_start": args.seed_start,
        "base_seeds": args.base_seeds,
        "severity": args.severity,
        "budget": args.budget,
        "beam_width": args.beam_width,
        "max_depth": args.max_depth,
        "route_samples": args.route_samples,
        "surface_grid": args.surface_grid,
        "ablation_stride": args.ablation_stride,
        "procedural_layout_count": len(
            {task["base_seed"] for task in tasks if task["source"] == "procedural"}
        ),
        "llm_layout_count": len(
            {
                task["overrides"]["layout_id"]
                for task in tasks
                if task["source"] == "llm"
            }
        )
        if any(task["source"] == "llm" for task in tasks)
        else 0,
        "procedural_manifest_sha256": (
            hashlib.sha256(args.procedural_manifest.read_bytes()).hexdigest()
            if args.procedural_manifest
            else None
        ),
        "llm_manifest_sha256": (
            hashlib.sha256(args.llm_manifest.read_bytes()).hexdigest()
            if args.llm_manifest
            else None
        ),
        "task_ids": sorted(task_ids),
        "code_sha256": {
            "run_full.py": file_hash(Path(__file__).resolve()),
            "formal_benchmark.py": file_hash(
                Path(__file__).resolve().with_name("formal_benchmark.py")
            ),
            "revealrepair_core.py": file_hash(
                Path(__file__).resolve().parents[1]
                / "03_pilot"
                / "revealrepair_core.py"
            ),
        },
    }
    frozen_config["protocol_sha256"] = canonical_hash(frozen_config)
    config_path = args.output / "frozen_config.json"
    if config_path.exists():
        with config_path.open("r", encoding="utf-8") as handle:
            previous = json.load(handle)
        if previous != frozen_config:
            raise RuntimeError("output directory already contains a different frozen protocol")
    else:
        with config_path.open("w", encoding="utf-8") as handle:
            json.dump(frozen_config, handle, ensure_ascii=False, indent=2)

    checkpoint_path = args.output / "completed.jsonl"
    failure_path = args.output / "failures.jsonl"
    completed = load_completed(checkpoint_path)
    pending = [task for task in tasks if str(task["task_id"]) not in completed]
    print(
        f"protocol={frozen_config['protocol_sha256']} tasks={len(tasks)} "
        f"completed={len(task_ids & completed.keys())} pending={len(pending)} workers={args.workers}",
        flush=True,
    )
    started = time.perf_counter()
    if pending:
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(run_case, task): task for task in pending}
            for index, future in enumerate(concurrent.futures.as_completed(futures), start=1):
                task = futures[future]
                task_id = str(task["task_id"])
                try:
                    result = future.result()
                except Exception as exc:
                    append_jsonl(
                        failure_path,
                        {
                            "task_id": task_id,
                            "error_type": type(exc).__name__,
                            "error": str(exc),
                            "traceback": traceback.format_exc(),
                        },
                    )
                    print(f"failed {task_id}: {type(exc).__name__}: {exc}", flush=True)
                    continue
                append_jsonl(checkpoint_path, result)
                completed[task_id] = result
                ours = next(
                    row
                    for row in result["rows"]
                    if row["method"] == "revealrepair_attributed"
                )
                print(
                    f"done {index}/{len(pending)} {task_id} "
                    f"loss={float(ours['schedule_loss']):.4f} "
                    f"edits={int(ours['edit_count'])} valid={int(ours['hard_valid'])}",
                    flush=True,
                )

    completed = load_completed(checkpoint_path)
    write_outputs(args.output, task_ids, completed)
    succeeded = len(task_ids & completed.keys())
    metadata = {
        "protocol_sha256": frozen_config["protocol_sha256"],
        "task_count": len(tasks),
        "succeeded": succeeded,
        "failed_or_missing": len(tasks) - succeeded,
        "elapsed_seconds_this_invocation": time.perf_counter() - started,
        "python": sys.version,
        "platform": platform.platform(),
        "workers": args.workers,
    }
    with (args.output / "run_metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, ensure_ascii=False, indent=2)
    print(json.dumps(metadata, indent=2), flush=True)
    if succeeded != len(tasks):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
