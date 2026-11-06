from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import zipfile
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial import cKDTree


EXCLUDE_TERMS = (
    "avengers",
    "disney",
    "guardians_of_the_galaxy",
    "lego",
    "marvel",
    "nickelodeon",
    "nintendo",
    "pokemon",
    "spiderman",
    "star_wars",
    "teenage_mutant_ninja_turtles",
    "transformers",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--candidate-audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--count", type=int, default=30)
    parser.add_argument("--samples", type=int, default=20_000)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def load_scene_mesh(path: Path) -> trimesh.Trimesh:
    loaded = trimesh.load(path, force="scene", process=False)
    if isinstance(loaded, trimesh.Scene):
        try:
            mesh = loaded.to_geometry()
        except AttributeError:
            mesh = loaded.dump(concatenate=True)
    else:
        mesh = loaded
    if not isinstance(mesh, trimesh.Trimesh):
        mesh = trimesh.util.concatenate(mesh)
    mesh.remove_unreferenced_vertices()
    return mesh


def normalize_mesh(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    result = mesh.copy()
    low, high = result.bounds
    scale = float((high - low).max())
    if not np.isfinite(scale) or scale <= 1e-12:
        raise ValueError("Degenerate mesh bounds")
    result.vertices = (np.asarray(result.vertices, dtype=np.float64) - (low + high) / 2.0) / scale
    return result


def load_fragments(archive: zipfile.ZipFile, object_name: str) -> tuple[list[trimesh.Trimesh], list[str]]:
    prefix = f"GSO/{object_name}_0/models/"
    names = [
        name
        for name in archive.namelist()
        if name.startswith(prefix)
        and name.endswith(".ply")
        and ("/model_b_0_fragment_" in name or "/model_r_0_fragment_" in name)
    ]
    if not names:
        prefixes = sorted(
            {
                name.split("/models/")[0] + "/models/"
                for name in archive.namelist()
                if name.startswith(f"GSO/{object_name}_") and "/models/" in name
            }
        )
        if len(prefixes) == 1:
            prefix = prefixes[0]
            names = [
                name
                for name in archive.namelist()
                if name.startswith(prefix)
                and name.endswith(".ply")
                and ("/model_b_0_fragment_" in name or "/model_r_0_fragment_" in name)
            ]
    if not names:
        raise FileNotFoundError(f"No break-0 fragments for {object_name}")

    meshes = []
    for name in sorted(names):
        mesh = trimesh.load_mesh(io.BytesIO(archive.read(name)), file_type="ply", process=True)
        if not isinstance(mesh, trimesh.Trimesh):
            raise TypeError(f"Unexpected fragment type for {name}: {type(mesh)!r}")
        if not mesh.is_watertight or not mesh.is_winding_consistent or not mesh.is_volume:
            raise ValueError(f"Fragment is not a valid closed volume: {name}")
        meshes.append(mesh)
    return meshes, sorted(names)


def align_geometric_breaks_to_gso(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    result = mesh.copy()
    vertices = np.asarray(result.vertices, dtype=np.float64)
    result.vertices = np.column_stack([vertices[:, 0], vertices[:, 2], -vertices[:, 1]])
    return result


def alignment_metrics(
    source: trimesh.Trimesh,
    solid_gt: trimesh.Trimesh,
    samples: int,
    seed: int,
) -> dict[str, float]:
    source_points, _ = trimesh.sample.sample_surface(source, samples, seed=seed)
    gt_points, _ = trimesh.sample.sample_surface(solid_gt, samples, seed=seed + 1)
    source_tree = cKDTree(source_points)
    gt_tree = cKDTree(gt_points)
    source_to_gt = gt_tree.query(source_points, k=1, workers=-1)[0]
    gt_to_source = source_tree.query(gt_points, k=1, workers=-1)[0]
    precision = float(np.mean(source_to_gt < 0.02))
    recall = float(np.mean(gt_to_source < 0.02))
    fscore = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    return {
        "surface_chamfer_l2": float(np.mean(source_to_gt**2) + np.mean(gt_to_source**2)),
        "surface_precision_0.02": precision,
        "surface_recall_0.02": recall,
        "surface_fscore_0.02": float(fscore),
        "surface_p95_distance": float(np.quantile(np.concatenate([source_to_gt, gt_to_source]), 0.95)),
    }


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    gt_root = args.output / "solid_gt"
    gt_root.mkdir(parents=True, exist_ok=True)
    candidates = json.loads(args.candidate_audit.read_text(encoding="utf-8"))
    records: list[dict[str, object]] = []

    with zipfile.ZipFile(args.archive) as archive:
        for index, candidate in enumerate(candidates, start=1):
            object_name = str(candidate["object_name"])
            record: dict[str, object] = {
                "object_name": object_name,
                "input_mesh_path": candidate["local_path"],
                "input_mesh_sha256": candidate["sha256"],
                "source_repo": candidate["source_repo"],
                "source_path": candidate["source_path"],
                "solid_source_repo": "tars-home/GeometricBreaks",
                "solid_source_archive": "GSO.zip",
                "excluded_name": any(term in object_name.lower() for term in EXCLUDE_TERMS),
            }
            try:
                fragments, fragment_names = load_fragments(archive, object_name)
                complete = trimesh.boolean.union(fragments, engine="manifold", check_volume=True)
                if not isinstance(complete, trimesh.Trimesh):
                    raise TypeError(f"Boolean union returned {type(complete)!r}")
                complete = normalize_mesh(align_geometric_breaks_to_gso(complete))
                source = normalize_mesh(load_scene_mesh(Path(str(candidate["local_path"]))))
                components = complete.split(only_watertight=False)
                metrics = alignment_metrics(source, complete, args.samples, 20260714 + index)
                gt_path = gt_root / object_name / "solid_gt.ply"
                gt_path.parent.mkdir(parents=True, exist_ok=True)
                complete.export(gt_path)
                record.update(
                    {
                        "fragment_paths": fragment_names,
                        "fragment_count": len(fragment_names),
                        "gt_path": str(gt_path),
                        "gt_sha256": sha256(gt_path),
                        "gt_vertices": int(len(complete.vertices)),
                        "gt_faces": int(len(complete.faces)),
                        "gt_watertight": bool(complete.is_watertight),
                        "gt_winding_consistent": bool(complete.is_winding_consistent),
                        "gt_is_volume": bool(complete.is_volume),
                        "gt_components": int(len(components)),
                        "gt_volume": abs(float(complete.volume)),
                        **metrics,
                    }
                )
                record["solid_gt_valid"] = bool(
                    complete.is_watertight
                    and complete.is_winding_consistent
                    and complete.is_volume
                    and len(components) <= 4
                    and math.isfinite(float(complete.volume))
                    and abs(float(complete.volume)) > 1e-8
                    and metrics["surface_fscore_0.02"] >= 0.95
                    and metrics["surface_p95_distance"] <= 0.02
                    and metrics["surface_chamfer_l2"] <= 2e-4
                )
                record["status"] = "audited"
            except Exception as error:
                record["status"] = "failed"
                record["solid_gt_valid"] = False
                record["error"] = repr(error)
            records.append(record)
            print(
                "SOLID_GT",
                index,
                len(candidates),
                object_name,
                record.get("solid_gt_valid"),
                record.get("surface_fscore_0.02"),
                record.get("gt_components"),
                flush=True,
            )
            (args.output / "solid_gt_audit.json").write_text(
                json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
            )

    valid = [
        row
        for row in records
        if row.get("solid_gt_valid") and not row.get("excluded_name")
    ]
    valid.sort(
        key=lambda row: (
            int(row.get("gt_components", 999)),
            -float(row.get("surface_fscore_0.02", 0.0)),
            str(row["object_name"]),
        )
    )
    selected = valid[: args.count]
    fields = [
        "object_id",
        "object_name",
        "input_mesh_path",
        "input_mesh_sha256",
        "gt_path",
        "gt_sha256",
        "gt_vertices",
        "gt_faces",
        "gt_components",
        "gt_volume",
        "surface_chamfer_l2",
        "surface_fscore_0.02",
        "surface_p95_distance",
        "source_repo",
        "source_path",
        "solid_source_repo",
        "solid_source_archive",
    ]
    with (args.output / "pilot30_manifest.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for index, row in enumerate(selected, start=1):
            writer.writerow({"object_id": f"gso_{index:03d}", **{key: row[key] for key in fields[1:]}})

    summary = {
        "input_source_repo": "huanngzh/Edit3D-Bench",
        "solid_source_repo": "tars-home/GeometricBreaks",
        "solid_source_doi": "10.57967/hf/5592",
        "archive_sha256": sha256(args.archive),
        "candidates": len(candidates),
        "audited": sum(row.get("status") == "audited" for row in records),
        "valid_before_name_exclusions": sum(bool(row.get("solid_gt_valid")) for row in records),
        "valid_after_name_exclusions": len(valid),
        "selected": len(selected),
        "requested": args.count,
        "gate_passed": len(selected) == args.count,
        "alignment_transform": "(x, y, z)_GeometricBreaks -> (x, z, -y)_GSO",
        "selection_thresholds": {
            "watertight": True,
            "winding_consistent": True,
            "is_volume": True,
            "max_components": 4,
            "min_surface_fscore_0.02": 0.95,
            "max_surface_p95_distance": 0.02,
            "max_surface_chamfer_l2": 0.0002,
        },
    }
    (args.output / "solid_gt_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("SUMMARY", json.dumps(summary, ensure_ascii=False), flush=True)
    return 0 if summary["gate_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
