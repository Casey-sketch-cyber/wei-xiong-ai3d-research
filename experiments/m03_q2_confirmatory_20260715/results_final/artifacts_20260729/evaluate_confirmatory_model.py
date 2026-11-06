from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import os
import time
import traceback
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial import cKDTree


CALIBRATION_OBJECTS = tuple(f"gso_{index:03d}" for index in range(1, 11))
CALIBRATION_SEED = 20260714


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        choices=("triposr", "instantmesh", "hunyuan21", "trellis"),
        required=True,
    )
    parser.add_argument("--inference-root", type=Path, required=True)
    parser.add_argument("--deterministic-schedule", type=Path, required=True)
    parser.add_argument("--stochastic-schedule", type=Path, required=True)
    parser.add_argument("--d30-schedule", type=Path, required=True)
    parser.add_argument("--d30-results-root", type=Path, required=True)
    parser.add_argument("--trellis-calibration-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=10000)
    parser.add_argument("--calibration-samples", type=int, default=3000)
    parser.add_argument("--voxel-resolution", type=int, default=128)
    parser.add_argument("--grid-extent", type=float, default=1.5)
    parser.add_argument("--limit", type=int, default=0)
    return parser.parse_args()


def atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_seed(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_mesh(path: Path) -> trimesh.Trimesh:
    loaded = trimesh.load(path, process=False)
    if isinstance(loaded, trimesh.Scene):
        geometries = [
            geometry
            for geometry in loaded.geometry.values()
            if isinstance(geometry, trimesh.Trimesh)
        ]
        if not geometries:
            raise ValueError(f"No mesh geometry in {path}")
        loaded = trimesh.util.concatenate(geometries)
    if not isinstance(loaded, trimesh.Trimesh):
        raise TypeError(f"Unsupported geometry in {path}: {type(loaded)!r}")

    vertices = np.asarray(loaded.vertices, dtype=np.float64)
    faces = np.asarray(loaded.faces, dtype=np.int64)
    finite = np.isfinite(vertices).all(axis=1)
    index_valid = (faces >= 0).all(axis=1) & (faces < len(vertices)).all(axis=1)
    faces = faces[index_valid]
    face_valid = (
        finite[faces].all(axis=1)
        & (faces[:, 0] != faces[:, 1])
        & (faces[:, 1] != faces[:, 2])
        & (faces[:, 0] != faces[:, 2])
    )
    result = trimesh.Trimesh(vertices=vertices, faces=faces[face_valid], process=False)
    result.remove_unreferenced_vertices()
    if len(result.vertices) < 4 or len(result.faces) < 4:
        raise ValueError(f"Degenerate mesh in {path}")
    return result


def centered(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    result = mesh.copy()
    result.vertices = np.asarray(result.vertices) - result.bounds.mean(axis=0)
    return result


def transformed(mesh: trimesh.Trimesh, scale: float, rotation: np.ndarray) -> trimesh.Trimesh:
    result = centered(mesh)
    result.vertices = (np.asarray(result.vertices) * scale) @ rotation.T
    return result


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
    result = {
        "chamfer_l2": float(np.mean(pred_dist**2) + np.mean(gt_dist**2)),
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


def symmetric_chamfer(pred_points: np.ndarray, gt_points: np.ndarray) -> float:
    pred_tree = cKDTree(pred_points)
    gt_tree = cKDTree(gt_points)
    pred_dist, _ = query(gt_tree, pred_points)
    gt_dist, _ = query(pred_tree, gt_points)
    return float(np.mean(pred_dist**2) + np.mean(gt_dist**2))


def successful(model: str, row: dict) -> bool:
    if model == "instantmesh":
        return row.get("mesh_status") == "success"
    return row.get("status") == "success"


def result_path(root: Path, model: str) -> Path:
    names = {
        "triposr": "triposr_results.json",
        "instantmesh": "instantmesh_results.json",
        "hunyuan21": "hunyuan21_results.json",
        "trellis": "trellis_results.json",
    }
    return root / model / names[model]


def load_calibration_records(args: argparse.Namespace) -> list[dict]:
    if args.model == "trellis":
        path = args.trellis_calibration_root / "trellis_results.json"
    else:
        path = args.d30_results_root / {
            "triposr": "triposr_results.json",
            "instantmesh": "instantmesh_results.json",
            "hunyuan21": "hunyuan21_results.json",
        }[args.model]
    rows = json.loads(path.read_text(encoding="utf-8"))
    selected = []
    for row in rows:
        if row.get("object_id") not in CALIBRATION_OBJECTS or row.get("style") != "photo":
            continue
        if not successful(args.model, row):
            continue
        if args.model != "triposr" and int(row.get("seed", -1)) != CALIBRATION_SEED:
            continue
        if not row.get("mesh_path") or not Path(row["mesh_path"]).exists():
            continue
        selected.append(row)
    by_object = {row["object_id"]: row for row in selected}
    missing = sorted(set(CALIBRATION_OBJECTS) - set(by_object))
    if missing:
        raise ValueError(f"Missing {args.model} calibration records: {missing}")
    return [by_object[object_id] for object_id in CALIBRATION_OBJECTS]


def calibrate(args: argparse.Namespace) -> dict:
    manifest = {row["object_id"]: row for row in load_csv(args.d30_schedule)}
    records = load_calibration_records(args)
    pairs = []
    scale_ratios = []
    for row in records:
        object_id = row["object_id"]
        pred = centered(load_mesh(Path(row["mesh_path"])))
        gt = centered(load_mesh(Path(manifest[object_id]["gt_view_path"])))
        pred_extent = float(pred.extents.max())
        gt_extent = float(gt.extents.max())
        if pred_extent <= 0:
            raise ValueError(f"Zero calibration extent in {row['mesh_path']}")
        scale_ratios.append(gt_extent / pred_extent)
        pred_points, _ = sample_surface(
            pred, args.calibration_samples, stable_seed(args.model + object_id + ":cal_pred")
        )
        gt_points, _ = sample_surface(
            gt, args.calibration_samples, stable_seed(args.model + object_id + ":cal_gt")
        )
        pairs.append((pred_points, gt_points))

    scale = float(np.median(scale_ratios))
    candidates = signed_permutations()
    scores = []
    for matrix in candidates:
        scores.append(
            float(
                np.median(
                    [
                        symmetric_chamfer((pred_points * scale) @ matrix.T, gt_points)
                        for pred_points, gt_points in pairs
                    ]
                )
            )
        )
    best_index = int(np.argmin(scores))
    best = candidates[best_index]
    return {
        "model": args.model,
        "scale": scale,
        "matrix": best.tolist(),
        "determinant": float(np.linalg.det(best)),
        "median_calibration_chamfer": scores[best_index],
        "calibration_objects": list(CALIBRATION_OBJECTS),
        "calibration_seed": None if args.model == "triposr" else CALIBRATION_SEED,
        "scale_ratios": scale_ratios,
        "orientation_candidates": len(candidates),
        "calibration_samples": args.calibration_samples,
        "rule": "single global model scale and signed-axis transform frozen from ten D30 photos",
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


def normalize_seed(value: object) -> int:
    return -1 if value in (None, "", "None") else int(value)


def load_jobs(args: argparse.Namespace) -> list[dict]:
    schedule_path = (
        args.deterministic_schedule if args.model == "triposr" else args.stochastic_schedule
    )
    schedule = {
        (row["job_id"], normalize_seed(row.get("seed"))): row
        for row in load_csv(schedule_path)
    }
    path = result_path(args.inference_root, args.model)
    records = json.loads(path.read_text(encoding="utf-8"))
    jobs = []
    for result in records:
        seed = normalize_seed(result.get("seed"))
        key = (result["job_id"], seed)
        if key not in schedule:
            raise KeyError(f"Result absent from schedule: {key}")
        if not successful(args.model, result):
            continue
        if not result.get("mesh_path") or not Path(result["mesh_path"]).exists():
            continue
        source = schedule[key]
        if source["input_sha256"] != result["input_sha256"]:
            raise ValueError(f"Input hash mismatch for {key}")
        jobs.append({**source, **result, "seed": seed, "model": args.model})
    jobs.sort(key=lambda row: (row["job_id"], int(row["seed"])))
    expected = len(schedule)
    if len(jobs) != expected:
        raise ValueError(f"{args.model}: expected {expected} successful jobs, found {len(jobs)}")
    return jobs[: args.limit] if args.limit else jobs


def load_jsonl(path: Path) -> dict[tuple[str, int], dict]:
    records = {}
    if not path.exists():
        return records
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                if line_number == sum(1 for _ in path.open("r", encoding="utf-8")):
                    break
                raise
            records[(row["job_id"], int(row["seed"]))] = row
    return records


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def write_csv(path: Path, rows: list[dict]) -> None:
    columns = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    output = args.output_root / args.model
    output.mkdir(parents=True, exist_ok=True)
    calibration = calibrate(args)
    atomic_json(output / "calibration.json", calibration)
    jobs = load_jobs(args)

    results_path = output / "evaluation_results.jsonl"
    by_key = load_jsonl(results_path)
    gt_cache: dict[str, tuple[trimesh.Trimesh, np.ndarray]] = {}

    for index, job in enumerate(jobs, start=1):
        key = (job["job_id"], int(job["seed"]))
        if by_key.get(key, {}).get("evaluation_status") == "success":
            print("SKIP", index, len(jobs), key, flush=True)
            continue
        record = {
            "model": args.model,
            "job_id": job["job_id"],
            "object_id": job["object_id"],
            "object_name": job["object_name"],
            "split": job["split"],
            "view_id": job["view_id"],
            "style": job["style"],
            "severity": job["severity"],
            "seed": int(job["seed"]),
            "input_path": job["input_path"],
            "input_sha256": job["input_sha256"],
            "gt_view_path": job["gt_view_path"],
            "gt_view_sha256": job["gt_view_sha256"],
            "mesh_path": job["mesh_path"],
            "mesh_sha256": job.get("mesh_sha256", ""),
            "evaluation_status": "started",
        }
        print("START", index, len(jobs), key, flush=True)
        try:
            raw_pred = load_mesh(Path(job["mesh_path"]))
            pred = transformed(
                raw_pred,
                float(calibration["scale"]),
                np.asarray(calibration["matrix"], dtype=np.float64),
            )
            gt_key = job["gt_view_sha256"]
            if gt_key not in gt_cache:
                gt = centered(load_mesh(Path(job["gt_view_path"])))
                gt_voxels, _, _ = voxel_indices(
                    gt, args.voxel_resolution, args.grid_extent
                )
                gt_cache[gt_key] = (gt, gt_voxels)
            gt, gt_voxels = gt_cache[gt_key]

            started = time.time()
            record.update(topology_metrics(raw_pred))
            record.update(
                surface_metrics(
                    pred,
                    gt,
                    args.samples,
                    f"{args.model}:{job['job_id']}:{job['seed']}",
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
            record.update(
                {
                    "voxel_iou": float(intersection / union) if union else 0.0,
                    "solid_volume_ratio": float(pred_count / gt_count) if gt_count else math.nan,
                    "absolute_solid_volume_error": (
                        float(abs(pred_count - gt_count) / gt_count) if gt_count else math.nan
                    ),
                    "pred_voxel_count": pred_count,
                    "gt_voxel_count": gt_count,
                    "pred_voxels_before_grid_clip": pred_voxels_unclipped,
                    "voxel_clipped_fraction": clipped_fraction,
                    "x_extent_ratio": float(pred_extents[0] / gt_extents[0]),
                    "y_extent_ratio": float(pred_extents[1] / gt_extents[1]),
                    "z_extent_ratio": float(pred_extents[2] / gt_extents[2]),
                    "extent_relative_mae": float(
                        np.mean(np.abs(pred_extents - gt_extents) / gt_extents)
                    ),
                    "depth_extent_error": float(
                        abs(pred_extents[2] - gt_extents[2]) / gt_extents[2]
                    ),
                    "convex_hull_volume_ratio": float(
                        abs(pred.convex_hull.volume) / abs(gt.convex_hull.volume)
                    ),
                    "evaluation_status": "success",
                    "evaluation_seconds": round(time.time() - started, 3),
                }
            )
            print("DONE", index, len(jobs), key, record["evaluation_seconds"], flush=True)
        except Exception as error:
            record["evaluation_status"] = "failed"
            record["evaluation_error"] = repr(error)
            error_path = output / "errors" / f"{job['job_id']}__seed_{job['seed']}.txt"
            error_path.parent.mkdir(parents=True, exist_ok=True)
            error_path.write_text(traceback.format_exc(), encoding="utf-8")
            print("FAILED", index, len(jobs), key, repr(error), flush=True)
        append_jsonl(results_path, record)
        by_key[key] = record

    relevant = [by_key[(job["job_id"], int(job["seed"]))] for job in jobs]
    write_csv(output / "evaluation_results.csv", relevant)
    summary = {
        "model": args.model,
        "jobs_requested": len(jobs),
        "records": len(relevant),
        "success": sum(row.get("evaluation_status") == "success" for row in relevant),
        "failed": sum(row.get("evaluation_status") == "failed" for row in relevant),
        "samples": args.samples,
        "calibration_samples": args.calibration_samples,
        "voxel_resolution": args.voxel_resolution,
        "grid_extent": args.grid_extent,
        "deterministic_schedule_sha256": file_sha256(args.deterministic_schedule),
        "stochastic_schedule_sha256": file_sha256(args.stochastic_schedule),
        "d30_schedule_sha256": file_sha256(args.d30_schedule),
    }
    atomic_json(output / "evaluation_summary.json", summary)
    print("SUMMARY", json.dumps(summary), flush=True)
    return 0 if summary["failed"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())

