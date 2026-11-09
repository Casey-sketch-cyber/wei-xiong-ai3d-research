"""Merge re-evaluation shards and verify the camera protocol reproduces the frozen results.

    python -I experiments/m03_revision_20261109/merge_and_check.py \
        --reeval-root /root/autodl-tmp/m03_q2_confirmatory_20260715/revision_20261109/reeval \
        --frozen-root experiments/m03_q2_confirmatory_20260715/results_final/artifacts_20260729/evaluation

Writes <reeval-root>/<model>/reeval_results.csv and <reeval-root>/reproduction_check.json.
Exit code 0 only if every model has zero failed jobs and the camera protocol
matches the frozen F@0.05, F@0.1 and voxel IoU@128 within 1e-9 for every
job present in both tables.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

MODELS = ("triposr", "instantmesh", "hunyuan21", "trellis")
CHECKS = {
    "fscore_0.05": "camera_fscore_0.05",
    "fscore_0.1": "camera_fscore_0.1",
    "voxel_iou": "camera_voxel_iou_128",
    "chamfer_l2": "camera_chamfer_l2",
}
TOLERANCE = 1e-9


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reeval-root", type=Path, required=True)
    parser.add_argument("--frozen-root", type=Path, required=True,
                        help="folder with <model>/evaluation_results.csv from the frozen run")
    parser.add_argument("--models", type=str, default=",".join(MODELS))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = {"tolerance": TOLERANCE, "models": {}}
    ok = True
    for model in [name.strip() for name in args.models.split(",") if name.strip()]:
        shards = sorted((args.reeval_root / model).glob("reeval_shard*of*.csv"))
        if not shards:
            report["models"][model] = {"status": "no shards"}
            ok = False
            continue
        merged = pd.concat([pd.read_csv(path, encoding="utf-8-sig") for path in shards], ignore_index=True)
        merged = merged.drop_duplicates(subset=["job_id", "seed"], keep="last")
        merged.to_csv(args.reeval_root / model / "reeval_results.csv", index=False, encoding="utf-8-sig")
        failed = int((merged["reeval_status"] != "success").sum())

        frozen = pd.read_csv(args.frozen_root / model / "evaluation_results.csv", encoding="utf-8-sig")
        joined = merged.merge(frozen, on=["job_id", "seed"], how="inner", suffixes=("", "_frozen"))
        differences = {}
        for frozen_column, new_column in CHECKS.items():
            if new_column not in joined or frozen_column not in joined:
                differences[frozen_column] = "missing column"
                ok = False
                continue
            left = joined[new_column].astype(float)
            right = joined[frozen_column].astype(float) if frozen_column not in merged else joined[f"{frozen_column}_frozen"].astype(float)
            differences[frozen_column] = float((left - right).abs().max()) if len(joined) else None
        reproduced = all(isinstance(v, float) and v <= TOLERANCE for v in differences.values())
        ok = ok and failed == 0 and reproduced and len(joined) == len(merged)
        report["models"][model] = {
            "jobs": int(len(merged)),
            "failed": failed,
            "matched_with_frozen": int(len(joined)),
            "max_abs_difference": differences,
            "camera_reproduces_frozen": reproduced,
        }
    report["all_pass"] = ok
    (args.reeval_root / "reproduction_check.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
