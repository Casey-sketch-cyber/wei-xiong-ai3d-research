from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import time
import traceback
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial import cKDTree


CALIBRATION_SEED = 20260714


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument(
        "--models",
        nargs="+",
        choices=("triposr", "instantmesh", "hunyuan21"),
        default=("triposr", "instantmesh", "hunyuan21"),
    )
    parser.add_argument("--samples", type=int, default=10000)
    parser.add_argument("--calibration-samples", type=int, default=3000)
    parser.add_argument("--calibration-objects", type=int, default=5)
    parser.add_argument("--voxel-resolution", type=int, default=128)
    parser.add_argument("--grid-extent", type=float, default=1.5)
    parser.add_argument("--limit", type=int, default=0)
    return parser.parse_args()


def atomic_json(path: Path, data: object) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def load_manifest(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {(row["object_id"], row["style"]): row for row in rows}


def load_mesh(path: Path) -> trimesh.Trimesh:
    loaded = trimesh.load(path, process=False)
    if isinstance(loaded, trimesh.Scene):
        geometries = [item for item in loaded.geometry.values() if isinstance(item, trimesh.Trimesh)]
        if not geometries:
            raise ValueError(f"No mesh geometry in {path}")
        loaded = trimesh.util.concatenate(geometries)
    if not isinstance(loaded, trimesh.Trimesh):
        raise TypeError(f"Unsupported geometry in {path}: {type(loaded)!r}")

    vertices = np.asarray(loaded.vertices, dtype=np.float64)
    faces = np.asarray(loaded.faces, dtype=np.int64)
    finite = np.isfinite(vertices).all(axis=1)
    index_valid = (
        (faces >= 0).all(axis=1)
        & (faces < len(vertices)).all(axis=1)
    )
    faces = faces[index_valid]
    face_valid = (
        finite[faces].all(axis=1)
        & (faces[:, 0] != faces[:, 1])
        & (faces[:, 1] != faces[:, 2])
        & (faces[:, 0] != faces[:, 2])
    )
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces[face_valid], process=False)
    mesh.remove_unreferenced_vertices()
    if len(mesh.vertices) < 4 or len(mesh.faces) < 4:
        raise ValueError(f"Degenerate mesh in {path}")
    return mesh


def centered(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    result = mesh.copy()
    result.vertices = np.asarray(result.vertices) - result.bounds.mean(axis=0)
    return result


def transformed(mesh: trimesh.Trimesh, scale: float, rotation: np.ndarray) -> trimesh.Trimesh:
    result = centered(mesh)
    result.vertices = (np.asarray(result.vertices) * scale) @ rotation.T
    return result


def stable_seed(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)


def sample_surface(mesh: trimesh.Trimesh, count: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    triangles = np.asarray(mesh.triangles, dtype=np.float64)
    normals = np.asarray(mesh.face_normals, dtype=np.float64)
    areas = np.asarray(mesh.area_faces, dtype=np.float64)
    valid = np.isfinite(areas) & (areas > 0)
    triangles = triangles[valid]
    normals = normals[valid]
    areas = areas[valid]
    if len(areas) == 0 or areas.sum() <= 0:
        raise ValueError("Mesh has no sampleable surface")
    rng = np.random.default_rng(seed)
    face_index = rng.choice(len(areas), size=count, p=areas / areas.sum())
    selected = triangles[face_index]
    uv = rng.random((count, 2))
    reflected = uv.sum(axis=1) > 1.0
    uv[reflected] = 1.0 - uv[reflected]
    points = (
        selected[:, 0]
        + uv[:, :1] * (selected[:, 1] - selected[:, 0])
        + uv[:, 1:] * (selected[:, 2] - selected[:, 0])
    )
    return points, normals[face_index]


def query(tree: cKDTree, points: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    try:
        return tree.query(points, workers=-1)
    except TypeError:
        return tree.query(points)


def surface_metrics(pred: trimesh.Trimesh, gt: trimesh.Trimesh, count: int, tag: str) -> dict:
    pred_points, pred_normals = sample_surface(pred, count, stable_seed(tag + ":pred"))
    gt_points, gt_normals = sample_surface(gt, count, stable_seed(tag + ":gt"))
    gt_tree = cKDTree(gt_points)
    pred_tree = cKDTree(pred_points)
    pred_dist, pred_nn = query(gt_tree, pred_points)
    gt_dist, gt_nn = query(pred_tree, gt_points)
    chamfer_l2 = float(np.mean(pred_dist**2) + np.mean(gt_dist**2))
    result = {
        "chamfer_l2": chamfer_l2,
        "pred_to_gt_mean": float(np.mean(pred_dist)),
        "gt_to_pred_mean": float(np.mean(gt_dist)),
    }
    for threshold in (0.05, 0.1):
        precision = float(np.mean(pred_dist <= threshold))
        recall = float(np.mean(gt_dist <= threshold))
        result[f"precision_{threshold}"] = precision
        result[f"recall_{threshold}"] = recall
        result[f"fscore_{threshold}"] = (
            2.0 * precision * recall / (precision + recall)
            if precision + recall > 0
            else 0.0
        )
    normal_pg = np.abs(np.sum(pred_normals * gt_normals[pred_nn], axis=1))
    normal_gp = np.abs(np.sum(gt_normals * pred_normals[gt_nn], axis=1))
    result["normal_consistency"] = float(0.5 * (normal_pg.mean() + normal_gp.mean()))
    return result


def signed_permutations() -> list[np.ndarray]:
    matrices = []
    for permutation in itertools.permutations(range(3)):
        for signs in itertools.product((-1.0, 1.0), repeat=3):
            matrix = np.zeros((3, 3), dtype=np.float64)
            for row, column in enumerate(permutation):
                matrix[row, column] = signs[row]
            matrices.append(matrix)
    return matrices


def calibration_chamfer(pred_points: np.ndarray, gt_points: np.ndarray) -> float:
    pred_tree = cKDTree(pred_points)
    gt_tree = cKDTree(gt_points)
    pred_dist, _ = query(gt_tree, pred_points)
    gt_dist, _ = query(pred_tree, gt_points)
    return float(np.mean(pred_dist**2) + np.mean(gt_dist**2))


def calibrate_model(
    model: str,
    records: list[dict],
    manifest: dict[tuple[str, str], dict[str, str]],
    object_count: int,
    sample_count: int,
) -> dict:
    photos = [row for row in records if row["style"] == "photo"]
    stochastic = any(row.get("seed") is not None for row in photos)
    if stochastic:
        photos = [row for row in photos if int(row.get("seed", -1)) == CALIBRATION_SEED]
    photos = sorted(photos, key=lambda row: row["object_id"])[:object_count]
    if len(photos) < min(3, object_count):
        raise ValueError(f"{model} has only {len(photos)} calibration photos")

    pairs = []
    scale_ratios = []
    for row in photos:
        pred = centered(load_mesh(Path(row["mesh_path"])))
        gt_path = Path(manifest[(row["object_id"], "photo")]["gt_view_path"])
        gt = centered(load_mesh(gt_path))
        pred_extent = float(pred.extents.max())
        gt_extent = float(gt.extents.max())
        if pred_extent <= 0:
            raise ValueError(f"Zero extent in {row['mesh_path']}")
        scale_ratios.append(gt_extent / pred_extent)
        pred_points, _ = sample_surface(
            pred, sample_count, stable_seed(model + row["object_id"] + ":cal_pred")
        )
        gt_points, _ = sample_surface(
            gt, sample_count, stable_seed(model + row["object_id"] + ":cal_gt")
        )
        pairs.append((pred_points, gt_points))

    scale = float(np.median(scale_ratios))
    candidates = signed_permutations()
    candidate_scores = []
    for matrix in candidates:
        per_object = [
            calibration_chamfer((pred_points * scale) @ matrix.T, gt_points)
            for pred_points, gt_points in pairs
        ]
        candidate_scores.append(float(np.median(per_object)))
    best_index = int(np.argmin(candidate_scores))
    best = candidates[best_index]
    return {
        "model": model,
        "scale": scale,
        "matrix": best.tolist(),
        "determinant": float(np.linalg.det(best)),
        "median_calibration_chamfer": candidate_scores[best_index],
        "calibration_objects": [row["object_id"] for row in photos],
        "calibration_seed": CALIBRATION_SEED if stochastic else None,
        "scale_ratios": scale_ratios,
        "orientation_candidates": len(candidates),
        "rule": "single global model scale and signed-axis transform frozen from photo inputs",
    }


def voxel_indices(
    mesh: trimesh.Trimesh, resolution: int, grid_extent: float
) -> tuple[np.ndarray, float, int]:
    pitch = grid_extent / resolution
    lower = -grid_extent / 2.0
    voxels = mesh.voxelized(pitch, method="subdivide")
    voxels.fill()
    points = np.asarray(voxels.points)
    indices = np.floor((points - lower) / pitch).astype(np.int64)
    valid = ((indices >= 0) & (indices < resolution)).all(axis=1)
    clipped_fraction = 1.0 - float(valid.mean()) if len(valid) else 1.0
    indices = indices[valid]
    flat = np.ravel_multi_index(indices.T, (resolution, resolution, resolution))
    return np.unique(flat), clipped_fraction, int(len(points))


def topology_metrics(mesh: trimesh.Trimesh) -> dict:
    edges = np.asarray(mesh.edges_sorted)
    _, counts = np.unique(edges, axis=0, return_counts=True)
    try:
        components = int(mesh.body_count)
    except Exception:
        components = int(len(mesh.split(only_watertight=False)))
    return {
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "components": components,
        "boundary_edges": int(np.sum(counts == 1)),
        "nonmanifold_edges": int(np.sum(counts > 2)),
    }


def collect_model_records(work: Path, model: str) -> list[dict]:
    path = work / f"{model}_results.json"
    if model == "hunyuan21":
        path = work / "hunyuan21_results.json"
    if not path.exists():
        raise FileNotFoundError(path)
    source = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for row in source:
        success = row.get("mesh_status") == "success" if model == "instantmesh" else row.get("status") == "success"
        mesh_path = row.get("mesh_path")
        if success and mesh_path and Path(mesh_path).exists():
            rows.append({**row, "model": model})
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    columns = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    manifest = load_manifest(args.manifest)
    model_records = {model: collect_model_records(args.work, model) for model in args.models}
    calibrations = {
        model: calibrate_model(
            model,
            records,
            manifest,
            args.calibration_objects,
            args.calibration_samples,
        )
        for model, records in model_records.items()
    }
    atomic_json(args.work / "evaluation_calibration.json", calibrations)

    jobs = [row for model in args.models for row in model_records[model]]
    jobs.sort(key=lambda row: (row["model"], row["object_id"], row["style"], row.get("seed") or -1))
    if args.limit:
        jobs = jobs[: args.limit]

    results_path = args.work / "evaluation_results.json"
    previous = json.loads(results_path.read_text(encoding="utf-8")) if results_path.exists() else []
    by_key = {
        (row["model"], row["object_id"], row["style"], int(row["seed"])): row
        for row in previous
    }
    gt_cache: dict[str, tuple[trimesh.Trimesh, np.ndarray]] = {}

    for index, job in enumerate(jobs, start=1):
        seed = int(job["seed"]) if job.get("seed") is not None else -1
        key = (job["model"], job["object_id"], job["style"], seed)
        if key in by_key and by_key[key].get("evaluation_status") == "success":
            print("SKIP", index, len(jobs), key, flush=True)
            continue
        rec = {
            "model": job["model"],
            "object_id": job["object_id"],
            "object_name": job["object_name"],
            "style": job["style"],
            "seed": seed,
            "mesh_path": job["mesh_path"],
            "evaluation_status": "started",
        }
        by_key[key] = rec
        atomic_json(results_path, sorted(by_key.values(), key=lambda row: (row["model"], row["object_id"], row["style"], row["seed"])))
        print("START", index, len(jobs), key, flush=True)
        try:
            raw_pred = load_mesh(Path(job["mesh_path"]))
            calibration = calibrations[job["model"]]
            pred = transformed(
                raw_pred,
                float(calibration["scale"]),
                np.asarray(calibration["matrix"], dtype=np.float64),
            )
            if job["object_id"] not in gt_cache:
                gt_path = Path(manifest[(job["object_id"], job["style"])]["gt_view_path"])
                gt = centered(load_mesh(gt_path))
                gt_voxels, _, _ = voxel_indices(gt, args.voxel_resolution, args.grid_extent)
                gt_cache[job["object_id"]] = (gt, gt_voxels)
            gt, gt_voxels = gt_cache[job["object_id"]]

            started = time.time()
            rec.update(topology_metrics(raw_pred))
            rec.update(
                surface_metrics(
                    pred,
                    gt,
                    args.samples,
                    f"{job['model']}:{job['object_id']}:{job['style']}:{seed}",
                )
            )
            pred_voxels, clipped_fraction, pred_voxels_unclipped = voxel_indices(
                pred, args.voxel_resolution, args.grid_extent
            )
            intersection = len(np.intersect1d(pred_voxels, gt_voxels, assume_unique=True))
            union = len(pred_voxels) + len(gt_voxels) - intersection
            gt_count = len(gt_voxels)
            pred_count = len(pred_voxels)
            pred_extents = np.asarray(pred.extents)
            gt_extents = np.asarray(gt.extents)
            rec.update(
                {
                    "voxel_iou": float(intersection / union) if union else 0.0,
                    "solid_volume_ratio": float(pred_count / gt_count) if gt_count else math.nan,
                    "absolute_solid_volume_error": float(abs(pred_count - gt_count) / gt_count) if gt_count else math.nan,
                    "pred_voxel_count": pred_count,
                    "gt_voxel_count": gt_count,
                    "pred_voxels_before_grid_clip": pred_voxels_unclipped,
                    "voxel_clipped_fraction": clipped_fraction,
                    "x_extent_ratio": float(pred_extents[0] / gt_extents[0]),
                    "y_extent_ratio": float(pred_extents[1] / gt_extents[1]),
                    "z_extent_ratio": float(pred_extents[2] / gt_extents[2]),
                    "extent_relative_mae": float(np.mean(np.abs(pred_extents - gt_extents) / gt_extents)),
                    "depth_extent_error": float(abs(pred_extents[2] - gt_extents[2]) / gt_extents[2]),
                    "convex_hull_volume_ratio": float(abs(pred.convex_hull.volume) / abs(gt.convex_hull.volume)),
                    "evaluation_status": "success",
                    "evaluation_seconds": round(time.time() - started, 3),
                }
            )
            print("DONE", index, len(jobs), key, rec["evaluation_seconds"], flush=True)
        except Exception as error:
            rec["evaluation_status"] = "failed"
            rec["evaluation_error"] = repr(error)
            error_path = args.work / "evaluation_errors" / f"{job['model']}_{job['object_id']}_{job['style']}_{seed}.txt"
            error_path.parent.mkdir(parents=True, exist_ok=True)
            error_path.write_text(traceback.format_exc(), encoding="utf-8")
            print("FAILED", index, len(jobs), key, repr(error), flush=True)
        finally:
            atomic_json(results_path, sorted(by_key.values(), key=lambda row: (row["model"], row["object_id"], row["style"], row["seed"])))

    rows = sorted(by_key.values(), key=lambda row: (row["model"], row["object_id"], row["style"], row["seed"]))
    write_csv(args.work / "evaluation_results.csv", rows)
    summary = {
        "jobs_requested": len(jobs),
        "records": len(rows),
        "success": sum(row.get("evaluation_status") == "success" for row in rows),
        "failed": sum(row.get("evaluation_status") == "failed" for row in rows),
        "samples": args.samples,
        "calibration_samples": args.calibration_samples,
        "voxel_resolution": args.voxel_resolution,
        "grid_extent": args.grid_extent,
    }
    atomic_json(args.work / "evaluation_summary.json", summary)
    print("SUMMARY", json.dumps(summary), flush=True)
    return 0 if summary["failed"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
