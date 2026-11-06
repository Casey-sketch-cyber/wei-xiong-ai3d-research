from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    checks = (
        ("triposr", args.root / "inference/triposr/triposr_summary.json", "success", 1020),
        (
            "instantmesh",
            args.root / "inference/instantmesh/instantmesh_summary.json",
            "mesh_success",
            1740,
        ),
        (
            "hunyuan21",
            args.root / "inference/hunyuan21/hunyuan21_summary.json",
            "success",
            1740,
        ),
        ("trellis", args.root / "inference/trellis/trellis_summary.json", "success", 1740),
    )
    records = []
    failures = []
    for model, path, success_key, expected in checks:
        if not path.exists():
            row = {"model": model, "summary": str(path), "status": "missing"}
            failures.append(row)
            records.append(row)
            continue
        summary = json.loads(path.read_text(encoding="utf-8"))
        observed = int(summary.get(success_key, -1))
        failed = int(summary.get("failed", summary.get("mesh_failed", -1)))
        row = {
            "model": model,
            "summary": str(path),
            "success_key": success_key,
            "expected": expected,
            "observed": observed,
            "failed": failed,
            "status": "pass" if observed == expected and failed == 0 else "fail",
        }
        records.append(row)
        if row["status"] != "pass":
            failures.append(row)

    output = {
        "checks": records,
        "all_pass": not failures,
        "failures": failures,
    }
    (args.root / "inference_validation.json").write_text(
        json.dumps(output, indent=2), encoding="utf-8"
    )
    print(json.dumps(output, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())

