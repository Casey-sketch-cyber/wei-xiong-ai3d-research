from __future__ import annotations

import argparse
import csv
import json
import math
import os
from pathlib import Path

import nvdiffrast.torch as dr
import numpy as np
import torch
import trimesh


MODELS = ("triposr", "instantmesh", "hunyuan21", "trellis")
VIEWS = {
    "front": (0.0, 0.0, 1.0),
    "back": (0.0, 0.0, -1.0),
    "right": (1.0, 0.0, 0.0),
    "left": (-1.0, 0.0, 0.0),
    "top": (0.0, 1.0, 0.0),
    "bottom": (0.0, -1.0, 0.0),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluation-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--resolution", type=int, default=256)
    parser.add_argument("--grid-extent", type=float, default=1.5)
    parser.add_argument("--limit", type=int, default=0)
    return parser.parse_args()


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
    valid_indices = (faces >= 0).all(axis=1) & (faces < len(vertices)).all(axis=1)
    faces = faces[valid_indices]
    valid_faces = (
        finite[faces].all(axis=1)
        & (faces[:, 0] != faces[:, 1])
        & (faces[:, 1] != faces[:, 2])
        & (faces[:, 0] != faces[:, 2])
    )
    loaded = trimesh.Trimesh(vertices=vertices, faces=faces[valid_faces], process=False)
    loaded.remove_unreferenced_vertices()
    if len(loaded.vertices) < 4 or len(loaded.faces) < 4:
        raise ValueError(f"Degenerate mesh in {path}")
    return loaded


def transform_mesh(mesh: trimesh.Trimesh, scale: float, rotation: np.ndarray) -> trimesh.Trimesh:
    result = mesh.copy()
    vertices = np.asarray(result.vertices, dtype=np.float64)
    vertices = vertices - result.bounds.mean(axis=0)
    result.vertices = (vertices * scale) @ rotation.T
    return result


def centered(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    result = mesh.copy()
    result.vertices = np.asarray(result.vertices) - result.bounds.mean(axis=0)
    return result


def camera_basis(direction: tuple[float, float, float]) -> np.ndarray:
    forward = np.asarray(direction, dtype=np.float64)
    forward /= np.linalg.norm(forward)
    up_reference = np.asarray((0.0, 1.0, 0.0), dtype=np.float64)
    if abs(float(np.dot(forward, up_reference))) > 0.9:
        up_reference = np.asarray((0.0, 0.0, 1.0), dtype=np.float64)
    right = np.cross(up_reference, forward)
    right /= np.linalg.norm(right)
    up = np.cross(forward, right)
    up /= np.linalg.norm(up)
    return np.stack((right, up, forward), axis=0)


def render_mesh(
    context: dr.RasterizeCudaContext,
    mesh: trimesh.Trimesh,
    resolution: int,
    grid_extent: float,
) -> dict[str, tuple[torch.Tensor, torch.Tensor]]:
    vertices_np = np.asarray(mesh.vertices, dtype=np.float32)
    normals_np = np.asarray(mesh.vertex_normals, dtype=np.float32)
    faces_np = np.asarray(mesh.faces, dtype=np.int32)
    vertices = torch.from_numpy(vertices_np).cuda()
    normals = torch.from_numpy(normals_np).cuda()
    faces = torch.from_numpy(faces_np).cuda()
    half_extent = grid_extent / 2.0
    output = {}
    for name, direction in VIEWS.items():
        basis = torch.from_numpy(camera_basis(direction).astype(np.float32)).cuda()
        camera_vertices = vertices @ basis.T
        camera_normals = torch.nn.functional.normalize(normals @ basis.T, dim=-1)
        ones = torch.ones((len(vertices), 1), dtype=torch.float32, device="cuda")
        clip = torch.cat((camera_vertices / half_extent, ones), dim=1)[None]
        raster, _ = dr.rasterize(context, clip, faces, resolution=[resolution, resolution])
        mask = raster[0, :, :, 3] > 0
        interpolated, _ = dr.interpolate(camera_normals[None], raster, faces)
        rendered_normals = torch.nn.functional.normalize(interpolated[0], dim=-1)
        output[name] = (mask, rendered_normals)
    return output


def compare_renders(
    predicted: dict[str, tuple[torch.Tensor, torch.Tensor]],
    ground_truth: dict[str, tuple[torch.Tensor, torch.Tensor]],
) -> dict[str, float]:
    result = {}
    silhouette_values = []
    normal_values = []
    for name in VIEWS:
        pred_mask, pred_normals = predicted[name]
        gt_mask, gt_normals = ground_truth[name]
        union = pred_mask | gt_mask
        intersection = pred_mask & gt_mask
        union_count = int(union.sum().item())
        intersection_count = int(intersection.sum().item())
        silhouette = intersection_count / union_count if union_count else 0.0
        if union_count:
            cosine = torch.abs(torch.sum(pred_normals * gt_normals, dim=-1))
            normal_similarity = float(cosine[intersection].sum().item() / union_count)
        else:
            normal_similarity = 0.0
        result[f"silhouette_iou_{name}"] = float(silhouette)
        result[f"normal_render_similarity_{name}"] = normal_similarity
        silhouette_values.append(silhouette)
        normal_values.append(normal_similarity)
    result["silhouette_iou_mean"] = float(np.mean(silhouette_values))
    result["normal_render_similarity_mean"] = float(np.mean(normal_values))
    return result


def load_jobs(evaluation_root: Path) -> list[dict[str, str]]:
    jobs = []
    for model in MODELS:
        path = evaluation_root / model / "evaluation_results.csv"
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        for row in rows:
            if row["evaluation_status"] == "success" and row["split"] == "main":
                jobs.append(row)
    jobs.sort(key=lambda row: (row["object_id"], row["model"], row["job_id"], int(row["seed"])))
    return jobs


def load_previous(path: Path) -> dict[tuple[str, str, int], dict]:
    records = {}
    if not path.exists():
        return records
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                break
            records[(row["model"], row["job_id"], int(row["seed"]))] = row
    return records


def append_jsonl(path: Path, row: dict) -> None:
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
    args.output_root.mkdir(parents=True, exist_ok=True)
    jobs = load_jobs(args.evaluation_root)
    expected = 5040
    if len(jobs) != expected:
        raise ValueError(f"Expected {expected} main evaluation records, found {len(jobs)}")
    if args.limit:
        jobs = jobs[: args.limit]

    calibrations = {
        model: json.loads(
            (args.evaluation_root / model / "calibration.json").read_text(encoding="utf-8")
        )
        for model in MODELS
    }
    results_path = args.output_root / "render_diagnostics.jsonl"
    by_key = load_previous(results_path)
    context = dr.RasterizeCudaContext()

    grouped: dict[str, list[dict[str, str]]] = {}
    for job in jobs:
        grouped.setdefault(job["gt_view_sha256"], []).append(job)

    completed = 0
    for group_index, group_jobs in enumerate(grouped.values(), start=1):
        gt_path = Path(group_jobs[0]["gt_view_path"])
        gt_mesh = centered(load_mesh(gt_path))
        gt_render = render_mesh(context, gt_mesh, args.resolution, args.grid_extent)
        for job in group_jobs:
            key = (job["model"], job["job_id"], int(job["seed"]))
            if by_key.get(key, {}).get("render_status") == "success":
                completed += 1
                continue
            record = {
                "model": job["model"],
                "job_id": job["job_id"],
                "object_id": job["object_id"],
                "style": job["style"],
                "seed": int(job["seed"]),
                "mesh_path": job["mesh_path"],
                "mesh_sha256": job["mesh_sha256"],
                "gt_view_sha256": job["gt_view_sha256"],
                "resolution": args.resolution,
                "grid_extent": args.grid_extent,
                "render_status": "started",
            }
            try:
                calibration = calibrations[job["model"]]
                pred_mesh = transform_mesh(
                    load_mesh(Path(job["mesh_path"])),
                    float(calibration["scale"]),
                    np.asarray(calibration["matrix"], dtype=np.float64),
                )
                outside = np.any(
                    np.abs(np.asarray(pred_mesh.vertices)) > args.grid_extent / 2.0, axis=1
                )
                record["vertex_outside_standard_cube_fraction"] = float(np.mean(outside))
                pred_render = render_mesh(
                    context, pred_mesh, args.resolution, args.grid_extent
                )
                record.update(compare_renders(pred_render, gt_render))
                record["render_status"] = "success"
                del pred_render, pred_mesh
            except Exception as error:
                record["render_status"] = "failed"
                record["render_error"] = repr(error)
            append_jsonl(results_path, record)
            by_key[key] = record
            completed += 1
            print(
                "DONE",
                completed,
                len(jobs),
                group_index,
                len(grouped),
                key,
                record["render_status"],
                flush=True,
            )
        del gt_render, gt_mesh
        if group_index % 10 == 0:
            torch.cuda.empty_cache()

    relevant = [by_key[(job["model"], job["job_id"], int(job["seed"]))] for job in jobs]
    write_csv(args.output_root / "render_diagnostics.csv", relevant)
    summary = {
        "jobs_requested": len(jobs),
        "records": len(relevant),
        "success": sum(row.get("render_status") == "success" for row in relevant),
        "failed": sum(row.get("render_status") == "failed" for row in relevant),
        "resolution": args.resolution,
        "grid_extent": args.grid_extent,
        "views": list(VIEWS),
        "normal_similarity_rule": "absolute normal cosine over intersection, zero over silhouette mismatch, averaged over union",
    }
    (args.output_root / "render_diagnostics_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print("SUMMARY", json.dumps(summary), flush=True)
    return 0 if summary["failed"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
