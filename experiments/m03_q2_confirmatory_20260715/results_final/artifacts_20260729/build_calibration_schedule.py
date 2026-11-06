from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


CALIBRATION_OBJECTS = tuple(f"gso_{index:03d}" for index in range(1, 11))
CALIBRATION_SEED = 20260714


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    args = parse_args()
    with args.input_manifest.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    photos = {
        row["object_id"]: row
        for row in rows
        if row["style"] == "photo" and row["object_id"] in CALIBRATION_OBJECTS
    }
    missing = sorted(set(CALIBRATION_OBJECTS) - set(photos))
    if missing:
        raise ValueError(f"Missing calibration photos: {missing}")

    schedule = []
    for object_id in CALIBRATION_OBJECTS:
        source = photos[object_id]
        schedule.append(
            {
                "job_id": f"calibration--canonical--{object_id}--photo--medium",
                "object_id": object_id,
                "object_name": source["object_name"],
                "split": "calibration_d30",
                "view_id": "canonical",
                "style": "photo",
                "severity": "medium",
                "input_path": source["input_path"],
                "input_sha256": source["input_sha256"],
                "gt_view_path": source["gt_view_path"],
                "gt_view_sha256": source["gt_view_sha256"],
                "alpha_bbox": source["alpha_bbox"],
                "foreground_fraction": source["foreground_fraction"],
                "seed": CALIBRATION_SEED,
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(schedule[0]))
        writer.writeheader()
        writer.writerows(schedule)

    summary = {
        "source_manifest": str(args.input_manifest),
        "source_manifest_sha256": sha256(args.input_manifest),
        "schedule": str(args.output),
        "schedule_sha256": sha256(args.output),
        "objects": list(CALIBRATION_OBJECTS),
        "seed": CALIBRATION_SEED,
        "rule": "first ten D30 objects by frozen object_id; photo input only",
    }
    args.output.with_suffix(".summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

