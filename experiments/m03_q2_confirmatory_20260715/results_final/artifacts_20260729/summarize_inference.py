from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


MODELS = ("triposr", "instantmesh", "hunyuan21", "trellis")
RESULT_NAMES = {
    "triposr": "triposr_results.json",
    "instantmesh": "instantmesh_results.json",
    "hunyuan21": "hunyuan21_results.json",
    "trellis": "trellis_results.json",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def is_success(model: str, row: dict) -> bool:
    return (
        row.get("mesh_status") == "success"
        if model == "instantmesh"
        else row.get("status") == "success"
    )


def seconds(model: str, row: dict) -> float:
    if model == "instantmesh":
        return float(row["multiview_seconds"]) + float(row["mesh_seconds"])
    return float(row["seconds"])


def summarize(model: str, records: list[dict], scope: str) -> dict:
    if scope != "all":
        records = [row for row in records if row.get("split") == scope]
    times = np.asarray([seconds(model, row) for row in records], dtype=np.float64)
    faces = np.asarray([float(row.get("faces", np.nan)) for row in records], dtype=np.float64)
    vertices = np.asarray([float(row.get("vertices", np.nan)) for row in records], dtype=np.float64)
    watertight = np.asarray(
        [float(row.get("watertight", np.nan)) for row in records], dtype=np.float64
    )
    return {
        "model": model,
        "scope": scope,
        "records": int(len(records)),
        "total_inference_seconds": float(times.sum()),
        "total_inference_hours": float(times.sum() / 3600.0),
        "mean_seconds": float(times.mean()),
        "median_seconds": float(np.median(times)),
        "p95_seconds": float(np.quantile(times, 0.95)),
        "median_vertices": float(np.nanmedian(vertices)),
        "median_faces": float(np.nanmedian(faces)),
        "watertight_fraction": float(np.nanmean(watertight)),
        "timing_rule": "per-record model inference; InstantMesh includes multiview diffusion and mesh reconstruction",
    }


def main() -> int:
    args = parse_args()
    rows = []
    for model in MODELS:
        path = args.root / "inference" / model / RESULT_NAMES[model]
        records = [
            row
            for row in json.loads(path.read_text(encoding="utf-8"))
            if is_success(model, row)
        ]
        rows.append(summarize(model, records, "all"))
        rows.append(summarize(model, records, "main"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows)
    frame.to_csv(args.output, index=False)
    print(frame.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

