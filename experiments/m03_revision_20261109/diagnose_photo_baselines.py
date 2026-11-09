"""Reproduce the registration diagnosis from the frozen CSVs in this repository.

Runs locally without meshes or GPU:

    python -I experiments/m03_revision_20261109/diagnose_photo_baselines.py

Prints, for the photo condition of the main split, the medians that suggest
pose misregistration: solid volume ratio near 1 while voxel IoU stays low,
large per-axis extent error, and low six-view silhouette IoU even in the best
view. Writes the same table to results/diagnosis_photo_baselines.csv.
"""

from __future__ import annotations

import csv
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / "experiments" / "m03_q2_confirmatory_20260715" / "results_final" / "artifacts_20260729"
MODELS = ("triposr", "instantmesh", "hunyuan21", "trellis")
VIEWS = ("front", "back", "left", "right", "top", "bottom")


def read(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def median(rows: list[dict], key: str) -> float:
    return statistics.median(float(row[key]) for row in rows)


def main() -> int:
    render_rows = read(ARTIFACTS / "render_diagnostics" / "render_diagnostics.csv")
    table = []
    for model in MODELS:
        rows = [
            row for row in read(ARTIFACTS / "evaluation" / model / "evaluation_results.csv")
            if row["style"] == "photo" and row["split"] == "main"
        ]
        renders = [row for row in render_rows if row["model"] == model and row["style"] == "photo"]
        best_view = [max(float(row[f"silhouette_iou_{view}"]) for view in VIEWS) for row in renders]
        table.append({
            "model": model,
            "n_records": len(rows),
            "median_solid_volume_ratio": round(median(rows, "solid_volume_ratio"), 3),
            "median_voxel_iou": round(median(rows, "voxel_iou"), 3),
            "median_fscore_0.05": round(median(rows, "fscore_0.05"), 3),
            "median_extent_relative_mae": round(median(rows, "extent_relative_mae"), 3),
            "median_front_silhouette_iou": round(median(renders, "silhouette_iou_front"), 3),
            "share_best_view_silhouette_below_0.5": round(sum(v < 0.5 for v in best_view) / len(best_view), 3),
        })
    out_dir = Path(__file__).resolve().parent / "results"
    out_dir.mkdir(exist_ok=True)
    with (out_dir / "diagnosis_photo_baselines.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(table[0]))
        writer.writeheader()
        writer.writerows(table)
    for row in table:
        print(row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
