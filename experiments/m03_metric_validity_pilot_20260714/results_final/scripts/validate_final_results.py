from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd


EXPECTED = {
    "triposr": {"records": 180, "seeds": {-1}},
    "instantmesh": {"records": 360, "seeds": {20260714, 3407}},
    "hunyuan21": {"records": 360, "seeds": {20260714, 3407}},
}
PRIMARY_METRICS = (
    "fscore_0.05",
    "chamfer_l2",
    "voxel_iou",
    "solid_volume_ratio",
    "absolute_solid_volume_error",
    "normal_consistency",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with args.manifest.open("r", encoding="utf-8-sig", newline="") as handle:
        manifest = list(csv.DictReader(handle))
    manifest_keys = {(row["object_id"], row["style"]) for row in manifest}
    if len(manifest) != 180 or len(manifest_keys) != 180:
        raise ValueError(f"Expected 180 unique manifest rows, found {len(manifest_keys)}")

    data = pd.read_csv(args.work / "evaluation_results.csv")
    if len(data) != 900:
        raise ValueError(f"Expected 900 evaluation records, found {len(data)}")
    if not (data["evaluation_status"] == "success").all():
        raise ValueError("At least one evaluation record is not successful")
    keys = data[["model", "object_id", "style", "seed"]].apply(tuple, axis=1)
    if keys.nunique() != 900:
        raise ValueError("Evaluation keys are not unique")
    if set(zip(data["object_id"], data["style"])) != manifest_keys:
        raise ValueError("Evaluation object/style coverage differs from the frozen manifest")

    model_report = {}
    for model, expected in EXPECTED.items():
        subset = data[data["model"] == model]
        seeds = set(subset["seed"].astype(int).unique())
        if len(subset) != expected["records"] or seeds != expected["seeds"]:
            raise ValueError(
                f"{model} coverage mismatch: records={len(subset)}, seeds={sorted(seeds)}"
            )
        model_report[model] = {
            "records": len(subset),
            "seeds": [int(seed) for seed in sorted(seeds)],
            "objects": int(subset["object_id"].nunique()),
            "styles": int(subset["style"].nunique()),
        }

    values = data[list(PRIMARY_METRICS)].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("A primary metric contains NaN or infinity")
    severe_clip = int((data["voxel_clipped_fraction"] > 0.01).sum())

    calibration = json.loads(
        (args.work / "evaluation_calibration.json").read_text(encoding="utf-8")
    )
    if set(calibration) != set(EXPECTED):
        raise ValueError(f"Calibration coverage mismatch: {sorted(calibration)}")
    for model, record in calibration.items():
        if record.get("orientation_candidates") != 48 or record.get("scale", 0) <= 0:
            raise ValueError(f"Invalid calibration for {model}")

    report = {
        "valid": True,
        "manifest_rows": len(manifest),
        "evaluation_records": len(data),
        "models": model_report,
        "primary_metrics_finite": True,
        "records_with_voxel_clip_over_1pct": severe_clip,
        "calibrations": sorted(calibration),
    }
    path = args.work / "final_validation.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
