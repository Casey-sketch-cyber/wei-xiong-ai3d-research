#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import trimesh
from scipy.spatial import cKDTree


ISO_ROT = np.array(
    [
        [0.8192, 0.0, 0.5736],
        [0.2962, 0.8563, -0.4234],
        [-0.4912, 0.5165, 0.7010],
    ],
    dtype=np.float64,
)
STYLES = ("edge", "flat", "low_detail", "sketch", "watercolor")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--gt-root", type=Path, required=True)
    parser.add_argument("--triposr-csv", type=Path)
    parser.add_argument("--samples", type=int, default=15000)
    return parser.parse_args()


def normalize_points(points: np.ndarray) -> np.ndarray:
    points = np.asarray(points, dtype=np.float64)
    lo = points.min(axis=0)
    hi = points.max(axis=0)
    scale = float((hi - lo).max())
    if scale <= 1e-9:
        scale = 1.0
    return (points - (lo + hi) / 2.0) / scale


def load_mesh(path: Path) -> trimesh.Trimesh:
    loaded = trimesh.load(path, force="scene")
    if isinstance(loaded, trimesh.Scene):
        geometries = [
            geom for geom in loaded.geometry.values() if hasattr(geom, "vertices") and len(geom.vertices)
        ]
        if not geometries:
            raise ValueError(f"No geometry in {path}")
        mesh = trimesh.util.concatenate(geometries)
    else:
        mesh = loaded
    mesh.remove_unreferenced_vertices()
    return mesh


def surface_metrics(pred: np.ndarray, gt: np.ndarray) -> dict[str, float | str]:
    flips = {
        "identity": (1, 1, 1),
        "flip_x": (-1, 1, 1),
        "flip_y": (1, -1, 1),
        "flip_z": (1, 1, -1),
        "flip_xy": (-1, -1, 1),
        "flip_xz": (-1, 1, -1),
        "flip_yz": (1, -1, -1),
        "flip_xyz": (-1, -1, -1),
    }
    best = None
    for name, signs in flips.items():
        candidate = pred * np.asarray(signs)
        pred_tree = cKDTree(candidate)
        gt_tree = cKDTree(gt)
        d_pg, _ = gt_tree.query(candidate, k=1, workers=-1)
        d_gp, _ = pred_tree.query(gt, k=1, workers=-1)
        chamfer = float(np.mean(d_pg**2) + np.mean(d_gp**2))
        precision = float(np.mean(d_pg < 0.05))
        recall = float(np.mean(d_gp < 0.05))
        fscore = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
        current = {
            "alignment": name,
            "chamfer_l2": chamfer,
            "precision_0.05": precision,
            "recall_0.05": recall,
            "fscore_0.05": float(fscore),
        }
        if best is None or chamfer < best["chamfer_l2"]:
            best = current
    return best


def bootstrap_ci(values: np.ndarray, seed: int = 20260714) -> tuple[float, float]:
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return math.nan, math.nan
    rng = np.random.default_rng(seed)
    means = np.empty(5000, dtype=float)
    for index in range(len(means)):
        means[index] = rng.choice(values, size=len(values), replace=True).mean()
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def main() -> int:
    args = parse_args()
    out_dir = args.work / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)
    records = json.loads((args.work / "shape_results.json").read_text(encoding="utf-8"))
    records = [row for row in records if row.get("status") == "success"]

    gt_cache: dict[str, np.ndarray] = {}
    metric_rows = []
    for index, rec in enumerate(records, start=1):
        uid = rec["uid"]
        if uid not in gt_cache:
            gt_points = np.load(args.gt_root / uid / "gt_points.npy")
            gt_cache[uid] = normalize_points(gt_points @ ISO_ROT.T)
        mesh = load_mesh(Path(rec["output_glb"]))
        rng = np.random.default_rng(321 + int(rec["seed"]) % 100000)
        pred_points, _ = trimesh.sample.sample_surface(mesh, args.samples, seed=rng)
        metrics = surface_metrics(normalize_points(pred_points), gt_cache[uid])
        extents = np.asarray(mesh.extents, dtype=float)
        sorted_extents = np.sort(extents)
        try:
            convex_hull_volume = abs(float(mesh.convex_hull.volume))
        except Exception:
            convex_hull_volume = math.nan
        row = {
            "uid": uid,
            "name": rec["name"],
            "stratum": rec["stratum"],
            "style": rec["style"],
            "seed": int(rec["seed"]),
            "mesh_path": rec["output_glb"],
            "vertices": int(len(mesh.vertices)),
            "faces": int(len(mesh.faces)),
            "watertight": bool(mesh.is_watertight),
            "pred_volume": abs(float(mesh.volume)) if mesh.is_watertight else math.nan,
            "convex_hull_volume": convex_hull_volume,
            "extent_x": float(extents[0]),
            "extent_y": float(extents[1]),
            "extent_z": float(extents[2]),
            "extent_min": float(sorted_extents[0]),
            "extent_mid": float(sorted_extents[1]),
            "extent_max": float(sorted_extents[2]),
        }
        row.update(metrics)
        metric_rows.append(row)
        print("METRIC", index, len(records), uid, rec["style"], rec["seed"], flush=True)

    metrics_df = pd.DataFrame(metric_rows)
    metrics_df.to_csv(out_dir / "hunyuan21_metrics.csv", index=False)

    relative_rows = []
    for (uid, seed), group in metrics_df.groupby(["uid", "seed"]):
        photo = group[group["style"] == "photo"]
        if len(photo) != 1:
            continue
        photo = photo.iloc[0]
        for _, current in group[group["style"] != "photo"].iterrows():
            relative_rows.append(
                {
                    "uid": uid,
                    "name": current["name"],
                    "stratum": current["stratum"],
                    "style": current["style"],
                    "seed": int(seed),
                    "volume_ratio": current["pred_volume"] / photo["pred_volume"]
                    if np.isfinite(current["pred_volume"]) and photo["pred_volume"] > 0
                    else math.nan,
                    "convex_hull_volume_ratio": current["convex_hull_volume"]
                    / photo["convex_hull_volume"]
                    if np.isfinite(current["convex_hull_volume"])
                    and photo["convex_hull_volume"] > 0
                    else math.nan,
                    "min_extent_ratio": current["extent_min"] / photo["extent_min"],
                    "max_extent_ratio": current["extent_max"] / photo["extent_max"],
                    "delta_fscore_0.05": current["fscore_0.05"] - photo["fscore_0.05"],
                    "delta_chamfer_l2": current["chamfer_l2"] - photo["chamfer_l2"],
                }
            )
    relative_df = pd.DataFrame(relative_rows)
    relative_df.to_csv(out_dir / "hunyuan21_relative_to_photo.csv", index=False)

    aggregate = []
    for style, group in relative_df.groupby("style"):
        values = group["volume_ratio"].to_numpy(dtype=float)
        valid_values = values[np.isfinite(values)]
        ci_low, ci_high = bootstrap_ci(values)
        hull_values = group["convex_hull_volume_ratio"].to_numpy(dtype=float)
        valid_hull_values = hull_values[np.isfinite(hull_values)]
        hull_ci_low, hull_ci_high = bootstrap_ci(hull_values)
        aggregate.append(
            {
                "style": style,
                "n": int(len(group)),
                "objects": int(group["uid"].nunique()),
                "seeds": int(group["seed"].nunique()),
                "volume_ratio_valid_n": int(len(valid_values)),
                "mean_volume_ratio": float(np.nanmean(values)),
                "median_volume_ratio": float(np.nanmedian(values)),
                "mean_volume_ratio_ci_low": ci_low,
                "mean_volume_ratio_ci_high": ci_high,
                "pct_volume_ratio_below_0.8": float(np.mean(valid_values < 0.8) * 100)
                if len(valid_values)
                else math.nan,
                "convex_hull_volume_ratio_valid_n": int(len(valid_hull_values)),
                "mean_convex_hull_volume_ratio": float(np.nanmean(hull_values)),
                "median_convex_hull_volume_ratio": float(np.nanmedian(hull_values)),
                "mean_convex_hull_volume_ratio_ci_low": hull_ci_low,
                "mean_convex_hull_volume_ratio_ci_high": hull_ci_high,
                "pct_convex_hull_volume_ratio_below_0.8": float(
                    np.mean(valid_hull_values < 0.8) * 100
                )
                if len(valid_hull_values)
                else math.nan,
                "mean_min_extent_ratio": float(group["min_extent_ratio"].mean()),
                "mean_delta_fscore_0.05": float(group["delta_fscore_0.05"].mean()),
                "mean_delta_chamfer_l2": float(group["delta_chamfer_l2"].mean()),
            }
        )
    aggregate_df = pd.DataFrame(aggregate).sort_values("style")
    aggregate_df.to_csv(out_dir / "hunyuan21_aggregate.csv", index=False)

    seed_rows = []
    for style, group in relative_df.groupby("style"):
        pivot = group.pivot(index="uid", columns="seed", values="convex_hull_volume_ratio").dropna()
        if pivot.shape[1] == 2:
            diff = np.abs(pivot.iloc[:, 0] - pivot.iloc[:, 1])
            seed_rows.append(
                {
                    "style": style,
                    "n": int(len(diff)),
                    "mean_abs_convex_hull_ratio_seed_difference": float(diff.mean()),
                    "median_abs_convex_hull_ratio_seed_difference": float(diff.median()),
                    "convex_hull_ratio_seed_correlation": float(
                        pivot.iloc[:, 0].corr(pivot.iloc[:, 1], method="spearman")
                    ),
                }
            )
    seed_df = pd.DataFrame(seed_rows)
    seed_df.to_csv(out_dir / "seed_stability.csv", index=False)

    comparison_summary = {}
    if args.triposr_csv and args.triposr_csv.exists():
        triposr = pd.read_csv(args.triposr_csv)
        triposr = triposr[triposr["style"] == "photo"][["uid", "fscore_0.05", "chamfer_l2"]]
        triposr = triposr.rename(
            columns={"fscore_0.05": "triposr_fscore_0.05", "chamfer_l2": "triposr_chamfer_l2"}
        )
        hunyuan_photo = (
            metrics_df[metrics_df["style"] == "photo"]
            .groupby(["uid", "name", "stratum"], as_index=False)[["fscore_0.05", "chamfer_l2"]]
            .mean()
            .rename(
                columns={"fscore_0.05": "hunyuan_fscore_0.05", "chamfer_l2": "hunyuan_chamfer_l2"}
            )
        )
        comparison = hunyuan_photo.merge(triposr, on="uid", how="left")
        comparison["delta_fscore_hunyuan_minus_triposr"] = (
            comparison["hunyuan_fscore_0.05"] - comparison["triposr_fscore_0.05"]
        )
        comparison["delta_chamfer_hunyuan_minus_triposr"] = (
            comparison["hunyuan_chamfer_l2"] - comparison["triposr_chamfer_l2"]
        )
        comparison.to_csv(out_dir / "photo_model_comparison.csv", index=False)
        comparison_summary = {
            "median_hunyuan_photo_fscore": float(comparison["hunyuan_fscore_0.05"].median()),
            "median_triposr_photo_fscore": float(comparison["triposr_fscore_0.05"].median()),
            "objects_hunyuan_fscore_better": int(
                (comparison["delta_fscore_hunyuan_minus_triposr"] > 0).sum()
            ),
            "objects_compared": int(len(comparison)),
        }

    provisional = {
        "shape_success": int(len(metrics_df)),
        "shape_expected": 144,
        "watertight_rate": float(metrics_df["watertight"].mean()),
        "styles_with_median_convex_hull_volume_ratio_below_0.8": int(
            (aggregate_df["median_convex_hull_volume_ratio"] < 0.8).sum()
        ),
        "median_convex_hull_ratio_seed_abs_difference": float(
            seed_df["median_abs_convex_hull_ratio_seed_difference"].median()
        ),
        "photo_model_comparison": comparison_summary,
        "requires_visual_review": True,
    }
    (out_dir / "pilot_summary.json").write_text(
        json.dumps(provisional, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    lines = [
        "# Hunyuan3D 2.1 pilot report",
        "",
        f"- Successful shapes: {provisional['shape_success']} / {provisional['shape_expected']}",
        f"- Watertight rate: {provisional['watertight_rate']:.3f}",
        "- Strict mesh volume is reported only for watertight outputs; convex-hull envelope volume covers all valid meshes.",
        f"- Styles with median convex-hull volume ratio below 0.8: {provisional['styles_with_median_convex_hull_volume_ratio_below_0.8']} / 5",
        f"- Median convex-hull ratio seed difference: {provisional['median_convex_hull_ratio_seed_abs_difference']:.3f}",
        "",
        "## Relative-to-photo aggregate",
        "",
        aggregate_df.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Seed stability",
        "",
        seed_df.to_markdown(index=False, floatfmt=".4f"),
        "",
        "Visual review of the geometry and official PBR outputs is required before a full rerun.",
    ]
    if comparison_summary:
        lines.extend(
            [
                "",
                "## Photo baseline comparison",
                "",
                json.dumps(comparison_summary, ensure_ascii=False, indent=2),
            ]
        )
    (out_dir / "pilot_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(provisional, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
