"""Re-evaluate frozen M03 meshes under three registration protocols.

No model inference is run. For every completed reconstruction this script
computes the same metrics as the frozen evaluator under:

* ``camera``: the original frozen protocol (model-level scale + signed axis
  matrix, bbox centring). Its F@0.05/F@0.1/IoU@128 must reproduce the frozen
  evaluation_results.csv; ``check_camera_reproduction.py`` verifies this.
* ``rigid``: per-sample rotation + translation search, scale kept from the
  frozen calibration (pose error removed, scale error kept).
* ``sim``: per-sample rotation + translation + uniform scale (shape-only).

The per-sample transforms are stored so render diagnostics can be redone.
Outputs go to a NEW directory; frozen results are never modified.

Example (pilot, run on the server from the repository root):

    python -I experiments/m03_revision_20261109/reevaluate_aligned.py \
        --model hunyuan21 \
        --inference-root /root/autodl-tmp/m03_q2_confirmatory_20260715/inference \
        --deterministic-schedule experiments/m03_q2_confirmatory_20260715/inference_schedule_deterministic.csv \
        --stochastic-schedule experiments/m03_q2_confirmatory_20260715/inference_schedule_stochastic.csv \
        --frozen-calibration /root/autodl-tmp/m03_q2_confirmatory_20260715/evaluation/hunyuan21/calibration.json \
        --output-root /root/autodl-tmp/m03_q2_confirmatory_20260715/revision_20261109/reeval \
        --styles photo --split main --object-limit 20
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time
import traceback
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import alignment_core as ac  # noqa: E402

FROZEN_EVALUATOR = HERE.parent / "m03_q2_confirmatory_20260715" / "evaluate_confirmatory_model.py"
THRESHOLDS = (0.02, 0.05, 0.1, 0.2)
PROTOCOLS = ("camera", "rigid", "sim")


def load_frozen_evaluator():
    spec = importlib.util.spec_from_file_location("frozen_eval", FROZEN_EVALUATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fe = load_frozen_evaluator()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=("triposr", "instantmesh", "hunyuan21", "trellis"), required=True)
    parser.add_argument("--inference-root", type=Path, required=True)
    parser.add_argument("--deterministic-schedule", type=Path, required=True)
    parser.add_argument("--stochastic-schedule", type=Path, required=True)
    parser.add_argument("--frozen-calibration", type=Path, required=True,
                        help="calibration.json written by the frozen evaluator for this model")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=10000, help="metric samples (frozen value 10000)")
    parser.add_argument("--alignment-samples", type=int, default=6000)
    parser.add_argument("--random-rotations", type=int, default=ac.DEFAULT_RANDOM_ROTATIONS)
    parser.add_argument("--voxel-resolutions", type=str, default="64,128",
                        help="comma list; 128 is the frozen resolution, 256 is slow")
    parser.add_argument("--grid-extent", type=float, default=1.5)
    parser.add_argument("--split", type=str, default="", help="main / view / severity; empty = all")
    parser.add_argument("--styles", type=str, default="", help="comma list; empty = all")
    parser.add_argument("--object-limit", type=int, default=0, help="first N objects by id (pilot)")
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--num-shards", type=int, default=1)
    return parser.parse_args()


def select_jobs(args: argparse.Namespace) -> list[dict]:
    frozen_args = argparse.Namespace(
        model=args.model,
        deterministic_schedule=args.deterministic_schedule,
        stochastic_schedule=args.stochastic_schedule,
        inference_root=args.inference_root,
        limit=0,
    )
    jobs = fe.load_jobs(frozen_args)
    if args.split:
        jobs = [job for job in jobs if job["split"] == args.split]
    if args.styles:
        wanted = {style.strip() for style in args.styles.split(",") if style.strip()}
        jobs = [job for job in jobs if job["style"] in wanted]
    if args.object_limit:
        objects = sorted({job["object_id"] for job in jobs})[: args.object_limit]
        keep = set(objects)
        jobs = [job for job in jobs if job["object_id"] in keep]
    return [job for index, job in enumerate(jobs) if index % args.num_shards == args.shard]


def surface_metrics_multi(pred, gt, count: int, tag: str) -> dict:
    """Same sampling and formulas as the frozen evaluator, more thresholds."""
    pred_points, pred_normals = fe.sample_surface(pred, count, fe.stable_seed(tag + ":pred"))
    gt_points, gt_normals = fe.sample_surface(gt, count, fe.stable_seed(tag + ":gt"))
    gt_tree = cKDTree(gt_points)
    pred_tree = cKDTree(pred_points)
    pred_dist, pred_nn = fe.query(gt_tree, pred_points)
    gt_dist, gt_nn = fe.query(pred_tree, gt_points)
    result = {
        "chamfer_l2": float(np.mean(pred_dist**2) + np.mean(gt_dist**2)),
        "pred_to_gt_mean": float(np.mean(pred_dist)),
        "gt_to_pred_mean": float(np.mean(gt_dist)),
    }
    for threshold in THRESHOLDS:
        precision = float(np.mean(pred_dist <= threshold))
        recall = float(np.mean(gt_dist <= threshold))
        result[f"precision_{threshold}"] = precision
        result[f"recall_{threshold}"] = recall
        result[f"fscore_{threshold}"] = (
            2.0 * precision * recall / (precision + recall) if precision + recall > 0 else 0.0
        )
    normal_pg = np.abs(np.sum(pred_normals * gt_normals[pred_nn], axis=1))
    normal_gp = np.abs(np.sum(gt_normals * pred_normals[gt_nn], axis=1))
    result["normal_consistency"] = float(0.5 * (normal_pg.mean() + normal_gp.mean()))
    return result


def solid_metrics(pred, gt, gt_voxels: dict, resolutions: list[int], extent: float) -> dict:
    result = {}
    for resolution in resolutions:
        pred_voxels, clipped, _ = fe.voxel_indices(pred, resolution, extent)
        gt_set = gt_voxels[resolution]
        intersection = len(np.intersect1d(pred_voxels, gt_set, assume_unique=True))
        union = len(pred_voxels) + len(gt_set) - intersection
        result[f"voxel_iou_{resolution}"] = float(intersection / union) if union else 0.0
        result[f"solid_volume_ratio_{resolution}"] = (
            float(len(pred_voxels) / len(gt_set)) if len(gt_set) else math.nan
        )
        result[f"voxel_clipped_fraction_{resolution}"] = clipped
    pred_extents = np.asarray(pred.extents)
    gt_extents = np.asarray(gt.extents)
    result["extent_relative_mae"] = float(np.mean(np.abs(pred_extents - gt_extents) / gt_extents))
    return result


def moved_mesh(mesh, rotation, scale, translation):
    result = mesh.copy()
    result.vertices = ac.apply_transform(np.asarray(mesh.vertices), rotation, scale, translation)
    return result


def main() -> int:
    args = parse_args()
    resolutions = [int(value) for value in args.voxel_resolutions.split(",") if value.strip()]
    calibration = json.loads(args.frozen_calibration.read_text(encoding="utf-8"))
    output = args.output_root / args.model
    output.mkdir(parents=True, exist_ok=True)
    results_path = output / f"reeval_shard{args.shard}of{args.num_shards}.jsonl"
    done = fe.load_jsonl(results_path)
    jobs = select_jobs(args)
    gt_cache: dict[str, tuple] = {}

    run_info = {
        "model": args.model,
        "frozen_calibration": str(args.frozen_calibration),
        "frozen_calibration_sha256": fe.file_sha256(args.frozen_calibration),
        "alignment_core_sha256": fe.file_sha256(HERE / "alignment_core.py"),
        "samples": args.samples,
        "alignment_samples": args.alignment_samples,
        "random_rotations": args.random_rotations,
        "voxel_resolutions": resolutions,
        "grid_extent": args.grid_extent,
        "thresholds": list(THRESHOLDS),
        "selected_jobs": len(jobs),
        "filters": {"split": args.split, "styles": args.styles, "object_limit": args.object_limit,
                    "shard": args.shard, "num_shards": args.num_shards},
    }
    fe.atomic_json(output / f"run_info_shard{args.shard}of{args.num_shards}.json", run_info)

    for index, job in enumerate(jobs, start=1):
        key = (job["job_id"], int(job["seed"]))
        if done.get(key, {}).get("reeval_status") == "success":
            continue
        record = {
            "model": args.model,
            "job_id": job["job_id"],
            "object_id": job["object_id"],
            "split": job["split"],
            "view_id": job["view_id"],
            "style": job["style"],
            "severity": job["severity"],
            "seed": int(job["seed"]),
            "mesh_path": job["mesh_path"],
            "gt_view_path": job["gt_view_path"],
            "reeval_status": "started",
        }
        started = time.time()
        try:
            raw = fe.load_mesh(Path(job["mesh_path"]))
            pred_camera = fe.transformed(
                raw, float(calibration["scale"]), np.asarray(calibration["matrix"], dtype=np.float64)
            )
            gt_key = job["gt_view_sha256"]
            if gt_key not in gt_cache:
                gt = fe.centered(fe.load_mesh(Path(job["gt_view_path"])))
                voxels = {res: fe.voxel_indices(gt, res, args.grid_extent)[0] for res in resolutions}
                gt_cache[gt_key] = (gt, voxels)
            gt, gt_voxels = gt_cache[gt_key]

            tag = f"{args.model}:{job['job_id']}:{job['seed']}"
            align_pred, _ = fe.sample_surface(pred_camera, args.alignment_samples, fe.stable_seed(tag + ":align_pred"))
            align_gt, _ = fe.sample_surface(gt, args.alignment_samples, fe.stable_seed(tag + ":align_gt"))
            transforms = {"camera": (np.eye(3), 1.0, np.zeros(3))}
            for mode, prefix in (("rigid", "rigid"), ("similarity", "sim")):
                result = ac.align(align_pred, align_gt, mode=mode, random_rotations=args.random_rotations)
                record.update(result.as_record(f"align_{prefix}_"))
                transforms[prefix] = (result.rotation, result.scale, result.translation)

            for protocol in PROTOCOLS:
                rotation, scale, translation = transforms[protocol]
                mesh = pred_camera if protocol == "camera" else moved_mesh(pred_camera, rotation, scale, translation)
                metrics = surface_metrics_multi(mesh, gt, args.samples, tag)
                metrics.update(solid_metrics(mesh, gt, gt_voxels, resolutions, args.grid_extent))
                record.update({f"{protocol}_{name}": value for name, value in metrics.items()})

            record.update(fe.topology_metrics(raw))
            record["reeval_status"] = "success"
            record["reeval_seconds"] = round(time.time() - started, 3)
            print("DONE", index, len(jobs), key, record["reeval_seconds"], flush=True)
        except Exception as error:  # keep going; failures are listed in the summary
            record["reeval_status"] = "failed"
            record["reeval_error"] = repr(error)
            error_dir = output / "errors"
            error_dir.mkdir(parents=True, exist_ok=True)
            (error_dir / f"{job['job_id']}__seed_{job['seed']}.txt").write_text(
                traceback.format_exc(), encoding="utf-8"
            )
            print("FAILED", index, len(jobs), key, repr(error), flush=True)
        fe.append_jsonl(results_path, record)
        done[key] = record

    rows = [done[(job["job_id"], int(job["seed"]))] for job in jobs]
    fe.write_csv(output / f"reeval_shard{args.shard}of{args.num_shards}.csv", rows)
    failed = sum(row.get("reeval_status") != "success" for row in rows)
    print("SUMMARY", json.dumps({"model": args.model, "jobs": len(rows), "failed": failed}), flush=True)
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
