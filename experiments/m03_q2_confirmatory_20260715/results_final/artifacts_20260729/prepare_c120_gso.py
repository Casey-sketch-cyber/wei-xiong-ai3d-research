from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import subprocess
import time
from pathlib import Path
from urllib.parse import quote

import numpy as np
import requests
import trimesh
from scipy.spatial import cKDTree


SALT = "m03-q2-confirmatory-20260715"
SOURCE_PREFIX = "GSO/"
SOURCE_SUFFIX = "/model.glb"
MANIFOLD_COMMIT = "a0cc6d9817f81efff63b704a2fed53567ea44cbd"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--discovery-manifest", type=Path, required=True)
    parser.add_argument("--manifold-bin", type=Path, required=True)
    parser.add_argument("--endpoint", default="https://hf-mirror.com")
    parser.add_argument("--source-repo", default="WalkerCH/stream3d")
    parser.add_argument("--target", type=int, default=120)
    parser.add_argument("--max-candidates", type=int, default=1030)
    parser.add_argument("--depth", type=int, default=8)
    parser.add_argument("--samples", type=int, default=20_000)
    parser.add_argument("--manifold-timeout", type=int, default=900)
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--reprocess-invalid", action="store_true")
    parser.add_argument("--allow-incomplete", action="store_true")
    return parser.parse_args()


def stable_hash(value: str) -> str:
    return hashlib.sha256(f"{SALT}:{value}".encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(4 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False),
        encoding="utf-8",
    )
    os.replace(temporary, path)


def repo_files(endpoint: str, repo_id: str) -> list[str]:
    response = requests.get(f"{endpoint}/api/datasets/{repo_id}", timeout=180)
    response.raise_for_status()
    payload = response.json()
    if payload.get("gated") or payload.get("private"):
        raise RuntimeError(f"Dataset unexpectedly gated or private: {repo_id}")
    paths = [
        str(item["rfilename"])
        for item in payload.get("siblings", [])
        if str(item.get("rfilename", "")).startswith(SOURCE_PREFIX)
        and str(item.get("rfilename", "")).endswith(SOURCE_SUFFIX)
    ]
    if not paths:
        raise RuntimeError(f"No GSO GLBs found in {repo_id}")
    return paths


def load_discovery_names(path: Path) -> set[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = csv.DictReader(handle)
        names = {str(row["object_name"]).strip() for row in rows}
    if not names:
        raise RuntimeError(f"Discovery manifest is empty: {path}")
    return names


def download(endpoint: str, repo_id: str, repo_path: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(target.suffix + ".part")
    url = f"{endpoint}/datasets/{repo_id}/resolve/main/{quote(repo_path, safe='/')}"
    for attempt in range(1, 8):
        headers: dict[str, str] = {}
        mode = "wb"
        if partial.exists() and partial.stat().st_size > 0:
            headers["Range"] = f"bytes={partial.stat().st_size}-"
            mode = "ab"
        try:
            with requests.get(url, headers=headers, stream=True, timeout=(45, 300)) as response:
                if response.status_code == 200 and mode == "ab":
                    mode = "wb"
                response.raise_for_status()
                with partial.open(mode) as handle:
                    for chunk in response.iter_content(4 * 1024 * 1024):
                        if chunk:
                            handle.write(chunk)
            os.replace(partial, target)
            return
        except Exception:
            if attempt == 7:
                raise
            time.sleep(5 * attempt)


def scene_to_mesh(path: Path) -> trimesh.Trimesh:
    loaded = trimesh.load(path, force="scene", process=False)
    if isinstance(loaded, trimesh.Scene):
        try:
            mesh = loaded.to_geometry()
        except AttributeError:
            dumped = loaded.dump(concatenate=True)
            mesh = dumped if isinstance(dumped, trimesh.Trimesh) else trimesh.util.concatenate(dumped)
    else:
        mesh = loaded
    if not isinstance(mesh, trimesh.Trimesh):
        mesh = trimesh.util.concatenate(mesh)
    if not isinstance(mesh, trimesh.Trimesh) or len(mesh.vertices) == 0 or len(mesh.faces) == 0:
        raise ValueError(f"No triangle mesh in {path}")
    mesh.remove_unreferenced_vertices()
    mesh.merge_vertices()
    if hasattr(mesh, "nondegenerate_faces"):
        mesh.update_faces(mesh.nondegenerate_faces())
    else:
        mesh.remove_degenerate_faces()
    mesh.remove_unreferenced_vertices()
    return mesh


def normalize_mesh(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    result = mesh.copy()
    low, high = np.asarray(result.bounds, dtype=np.float64)
    extent = high - low
    scale = float(extent.max())
    if not np.isfinite(scale) or scale <= 1e-12:
        raise ValueError("Degenerate source bounds")
    result.vertices = (
        np.asarray(result.vertices, dtype=np.float64) - (low + high) / 2.0
    ) / scale
    return result


def run_manifold(
    binary: Path,
    source_obj: Path,
    target_obj: Path,
    depth: int,
    timeout: int,
) -> subprocess.CompletedProcess[str]:
    target_obj.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            str(binary),
            "--input",
            str(source_obj),
            "--output",
            str(target_obj),
            "--depth",
            str(depth),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0 or not target_obj.exists() or target_obj.stat().st_size == 0:
        raise RuntimeError(
            f"ManifoldPlus failed ({result.returncode}): "
            f"{result.stderr[-2000:]} {result.stdout[-2000:]}"
        )
    return result


def query_distances(tree: cKDTree, points: np.ndarray) -> np.ndarray:
    try:
        return tree.query(points, k=1, workers=-1)[0]
    except TypeError:
        return tree.query(points, k=1)[0]


def surface_metrics(
    source: trimesh.Trimesh,
    repaired: trimesh.Trimesh,
    samples: int,
    seed: int,
) -> dict[str, float]:
    source_points, _ = trimesh.sample.sample_surface(source, samples, seed=seed)
    repaired_points, _ = trimesh.sample.sample_surface(repaired, samples, seed=seed + 1)
    source_to_repaired = query_distances(cKDTree(repaired_points), source_points)
    repaired_to_source = query_distances(cKDTree(source_points), repaired_points)
    precision = float(np.mean(source_to_repaired <= 0.02))
    recall = float(np.mean(repaired_to_source <= 0.02))
    fscore = 0.0 if precision + recall == 0 else 2.0 * precision * recall / (precision + recall)
    distances = np.concatenate([source_to_repaired, repaired_to_source])
    source_extents = np.asarray(source.extents, dtype=np.float64)
    repaired_extents = np.asarray(repaired.extents, dtype=np.float64)
    extent_relative_mae = float(
        np.mean(np.abs(repaired_extents - source_extents) / np.maximum(source_extents, 1e-8))
    )
    return {
        "surface_precision_0.02": precision,
        "surface_recall_0.02": recall,
        "surface_fscore_0.02": float(fscore),
        "surface_p95_distance": float(np.quantile(distances, 0.95)),
        "surface_chamfer_l2": float(
            np.mean(source_to_repaired**2) + np.mean(repaired_to_source**2)
        ),
        "extent_relative_mae": extent_relative_mae,
        "source_extent_x": float(source_extents[0]),
        "source_extent_y": float(source_extents[1]),
        "source_extent_z": float(source_extents[2]),
        "gt_extent_x": float(repaired_extents[0]),
        "gt_extent_y": float(repaired_extents[1]),
        "gt_extent_z": float(repaired_extents[2]),
    }


def accepted(record: dict[str, object]) -> bool:
    return bool(
        record.get("status") == "audited"
        and record.get("gt_watertight")
        and record.get("gt_winding_consistent")
        and record.get("gt_is_volume")
        and 1 <= int(record.get("gt_components", 999999)) <= 4
        and math.isfinite(float(record.get("gt_volume", float("nan"))))
        and float(record.get("gt_volume", 0.0)) > 1e-8
        and float(record.get("surface_fscore_0.02", 0.0)) >= 0.95
        and float(record.get("surface_p95_distance", float("inf"))) <= 0.02
        and float(record.get("surface_chamfer_l2", float("inf"))) <= 0.0002
        and float(record.get("extent_relative_mae", float("inf"))) <= 0.03
    )


def write_manifest(work: Path, records: list[dict[str, object]], target: int) -> None:
    selected = [row for row in records if bool(row.get("solid_gt_valid"))][:target]
    fields = [
        "object_id",
        "hash_rank",
        "candidate_hash",
        "object_name",
        "source_repo",
        "source_path",
        "input_mesh_path",
        "input_mesh_sha256",
        "normalized_source_path",
        "normalized_source_sha256",
        "gt_path",
        "gt_sha256",
        "gt_vertices",
        "gt_faces",
        "gt_components",
        "gt_volume",
        "surface_chamfer_l2",
        "surface_fscore_0.02",
        "surface_p95_distance",
        "extent_relative_mae",
        "manifold_commit",
        "manifold_depth",
    ]
    temporary = work / "c120_manifest.csv.tmp"
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for index, row in enumerate(selected, start=1):
            writer.writerow(
                {"object_id": f"c120_{index:03d}", **{key: row.get(key, "") for key in fields[1:]}}
            )
    os.replace(temporary, work / "c120_manifest.csv")


def main() -> int:
    args = parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    if not args.manifold_bin.exists():
        raise FileNotFoundError(args.manifold_bin)

    discovery = load_discovery_names(args.discovery_manifest)
    paths = repo_files(args.endpoint, args.source_repo)
    candidates: list[tuple[str, str, str]] = []
    for source_path in paths:
        object_name = source_path[len(SOURCE_PREFIX) : -len(SOURCE_SUFFIX)]
        if object_name not in discovery:
            candidates.append((stable_hash(object_name), object_name, source_path))
    candidates.sort(key=lambda row: (row[0], row[1]))
    candidates = candidates[: args.max_candidates]

    audit_path = args.work / "c120_audit.json"
    records: list[dict[str, object]] = []
    if audit_path.exists():
        records = json.loads(audit_path.read_text(encoding="utf-8"))
    by_name = {str(row["object_name"]): row for row in records}

    for hash_rank, (candidate_hash, object_name, source_path) in enumerate(candidates, start=1):
        already = by_name.get(object_name)
        if already is not None:
            retry_failed = args.retry_failed and already.get("status") != "audited"
            retry_invalid = args.reprocess_invalid and not bool(already.get("solid_gt_valid"))
            if not retry_failed and not retry_invalid:
                continue
        if sum(bool(row.get("solid_gt_valid")) for row in records) >= args.target:
            break

        object_dir = args.work / "candidates" / object_name
        input_path = object_dir / "model.glb"
        source_obj = object_dir / "normalized_source.obj"
        gt_path = object_dir / "solid_gt.obj"
        started = time.time()
        record: dict[str, object] = {
            "hash_rank": hash_rank,
            "candidate_hash": candidate_hash,
            "object_name": object_name,
            "source_repo": args.source_repo,
            "source_path": source_path,
            "input_mesh_path": str(input_path),
            "normalized_source_path": str(source_obj),
            "gt_path": str(gt_path),
            "manifold_commit": MANIFOLD_COMMIT,
            "manifold_depth": args.depth,
            "audit_samples": args.samples,
        }
        try:
            if not input_path.exists():
                download(args.endpoint, args.source_repo, source_path, input_path)
            record["input_mesh_bytes"] = int(input_path.stat().st_size)
            record["input_mesh_sha256"] = file_sha256(input_path)

            source = normalize_mesh(scene_to_mesh(input_path))
            source.export(source_obj, file_type="obj")
            record["normalized_source_sha256"] = file_sha256(source_obj)
            record["source_vertices"] = int(len(source.vertices))
            record["source_faces"] = int(len(source.faces))

            manifold = run_manifold(
                args.manifold_bin,
                source_obj,
                gt_path,
                args.depth,
                args.manifold_timeout,
            )
            repaired = trimesh.load_mesh(gt_path, process=False)
            if not isinstance(repaired, trimesh.Trimesh):
                repaired = trimesh.util.concatenate(repaired)
            repaired.remove_unreferenced_vertices()
            repaired.fix_normals(multibody=True)
            if math.isfinite(float(repaired.volume)) and float(repaired.volume) < 0:
                repaired.invert()
            repaired.export(gt_path, file_type="obj")
            components = repaired.split(only_watertight=False)
            seed = int(candidate_hash[:8], 16)
            metrics = surface_metrics(source, repaired, args.samples, seed)
            record.update(
                {
                    "gt_sha256": file_sha256(gt_path),
                    "gt_vertices": int(len(repaired.vertices)),
                    "gt_faces": int(len(repaired.faces)),
                    "gt_components": int(len(components)),
                    "gt_watertight": bool(repaired.is_watertight),
                    "gt_winding_consistent": bool(repaired.is_winding_consistent),
                    "gt_is_volume": bool(repaired.is_volume),
                    "gt_volume": abs(float(repaired.volume)),
                    "manifold_stdout_tail": manifold.stdout[-1000:],
                    "manifold_stderr_tail": manifold.stderr[-1000:],
                    **metrics,
                    "status": "audited",
                }
            )
            record["solid_gt_valid"] = accepted(record)
        except Exception as error:
            record["status"] = "failed"
            record["solid_gt_valid"] = False
            record["error"] = repr(error)
        record["elapsed_seconds"] = round(time.time() - started, 3)

        if already is not None:
            records[records.index(already)] = record
        else:
            records.append(record)
        records.sort(key=lambda row: (int(row.get("hash_rank", 10**9)), str(row["object_name"])))
        by_name[object_name] = record
        atomic_json(audit_path, records)
        write_manifest(args.work, records, args.target)
        print(
            "C120_AUDIT",
            hash_rank,
            len(candidates),
            object_name,
            "accepted=" + str(record["solid_gt_valid"]),
            "f02=" + str(record.get("surface_fscore_0.02")),
            "p95=" + str(record.get("surface_p95_distance")),
            "chamfer=" + str(record.get("surface_chamfer_l2")),
            "extent=" + str(record.get("extent_relative_mae")),
            "seconds=" + str(record["elapsed_seconds"]),
            flush=True,
        )

    accepted_records = [row for row in records if bool(row.get("solid_gt_valid"))]
    summary = {
        "status": "complete" if len(accepted_records) >= args.target else "incomplete",
        "protocol_salt": SALT,
        "source_repo": args.source_repo,
        "source_endpoint": args.endpoint,
        "source_glbs_found": len(paths),
        "discovery_objects_excluded": len(discovery),
        "eligible_candidates": len(paths) - len(discovery),
        "candidate_prefix_considered": len(candidates),
        "audited": sum(row.get("status") == "audited" for row in records),
        "failed": sum(row.get("status") == "failed" for row in records),
        "accepted": len(accepted_records),
        "target": args.target,
        "manifold_commit": MANIFOLD_COMMIT,
        "manifold_depth": args.depth,
        "thresholds": {
            "watertight": True,
            "winding_consistent": True,
            "positive_volume": True,
            "max_components": 4,
            "min_surface_fscore_0.02": 0.95,
            "max_surface_p95_distance": 0.02,
            "max_surface_chamfer_l2": 0.0002,
            "max_extent_relative_mae": 0.03,
        },
    }
    atomic_json(args.work / "c120_summary.json", summary)
    write_manifest(args.work, records, args.target)
    print("C120_SUMMARY", json.dumps(summary, ensure_ascii=False), flush=True)
    complete = len(accepted_records) >= args.target
    return 0 if complete or args.allow_incomplete else 2


if __name__ == "__main__":
    raise SystemExit(main())
