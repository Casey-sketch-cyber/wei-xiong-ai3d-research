from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from evaluate_confirmatory_model import load_mesh


MODELS = ("triposr", "instantmesh", "hunyuan21", "trellis")
FEATURES = (
    "gt_log_faces",
    "gt_surface_area",
    "gt_volume",
    "gt_solidity",
    "gt_elongation",
    "gt_middle_extent_ratio",
    "gt_bbox_fill",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schedule", type=Path, required=True)
    parser.add_argument("--analysis-root", type=Path, required=True)
    return parser.parse_args()


def load_schedule(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    photos = {
        row["object_id"]: row
        for row in rows
        if row["split"] == "main" and row["style"] == "photo"
    }
    if len(photos) != 120:
        raise ValueError(f"Expected 120 main photo records, found {len(photos)}")
    return [photos[object_id] for object_id in sorted(photos)]


def holm_adjust(values: list[float]) -> list[float]:
    order = np.argsort(values)
    output = np.empty(len(values), dtype=np.float64)
    running = 0.0
    for rank, index in enumerate(order):
        candidate = min(1.0, (len(values) - rank) * values[index])
        running = max(running, candidate)
        output[index] = running
    return output.tolist()


def morphology_record(row: dict[str, str]) -> dict:
    mesh = load_mesh(Path(row["gt_view_path"]))
    extents = np.sort(np.asarray(mesh.extents, dtype=np.float64))
    volume = float(abs(mesh.volume))
    hull_volume = float(abs(mesh.convex_hull.volume))
    bbox_volume = float(np.prod(extents))
    return {
        "object_id": row["object_id"],
        "object_name": row["object_name"],
        "gt_view_path": row["gt_view_path"],
        "gt_view_sha256": row["gt_view_sha256"],
        "gt_vertices": int(len(mesh.vertices)),
        "gt_faces": int(len(mesh.faces)),
        "gt_log_faces": float(np.log10(max(len(mesh.faces), 1))),
        "gt_components": int(mesh.body_count),
        "gt_watertight": bool(mesh.is_watertight),
        "gt_surface_area": float(mesh.area),
        "gt_volume": volume,
        "gt_convex_hull_volume": hull_volume,
        "gt_solidity": volume / hull_volume if hull_volume > 0 else np.nan,
        "gt_min_extent": float(extents[0]),
        "gt_middle_extent": float(extents[1]),
        "gt_max_extent": float(extents[2]),
        "gt_elongation": float(extents[0] / extents[2]) if extents[2] > 0 else np.nan,
        "gt_middle_extent_ratio": float(extents[1] / extents[2]) if extents[2] > 0 else np.nan,
        "gt_bbox_fill": volume / bbox_volume if bbox_volume > 0 else np.nan,
    }


def main() -> int:
    args = parse_args()
    args.analysis_root.mkdir(parents=True, exist_ok=True)
    morphology = pd.DataFrame([morphology_record(row) for row in load_schedule(args.schedule)])
    morphology.to_csv(args.analysis_root / "gt_morphology.csv", index=False)

    paired = pd.read_csv(args.analysis_root / "paired_main_object_averaged.csv")
    sketch = paired[paired["style"] == "sketch"].merge(
        morphology, on=["object_id"], how="inner", validate="many_to_one"
    )
    associations = []
    for model in MODELS:
        subset = sketch[sketch["model"] == model]
        model_rows = []
        for feature in FEATURES:
            valid = subset[[feature, "rg"]].dropna()
            test = spearmanr(valid[feature], valid["rg"])
            quartiles = pd.qcut(valid[feature], 4, labels=False, duplicates="drop")
            low = valid.loc[quartiles == quartiles.min(), "rg"].mean()
            high = valid.loc[quartiles == quartiles.max(), "rg"].mean()
            model_rows.append(
                {
                    "model": model,
                    "feature": feature,
                    "n_objects": int(len(valid)),
                    "spearman_rho": float(test.statistic),
                    "p_value": float(test.pvalue),
                    "high_minus_low_quartile_rg": float(high - low),
                    "analysis_status": "exploratory",
                }
            )
        adjusted = holm_adjust([row["p_value"] for row in model_rows])
        for row, p_holm in zip(model_rows, adjusted):
            row["p_holm_within_model"] = p_holm
        associations.extend(model_rows)
    pd.DataFrame(associations).to_csv(
        args.analysis_root / "morphology_rg_associations.csv", index=False
    )
    print(pd.DataFrame(associations).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

