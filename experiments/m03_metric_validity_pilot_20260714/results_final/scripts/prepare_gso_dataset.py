from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from pathlib import Path
from urllib.parse import quote

import numpy as np
import requests
import trimesh


REPO_ID = "huanngzh/Edit3D-Bench"
SOURCE_PREFIX = "data/GSO/"
SOURCE_SUFFIX = "/source_model/model.glb"
EXCLUDE_TERMS = (
    "avengers",
    "guardians_of_the_galaxy",
    "nintendo",
    "spiderman",
    "teenage_mutant_ninja_turtles",
    "transformers",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--endpoint", default="https://hf-mirror.com")
    parser.add_argument("--count", type=int, default=30)
    parser.add_argument("--candidate-limit", type=int, default=50)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def repo_files(endpoint: str) -> list[str]:
    response = requests.get(f"{endpoint}/api/datasets/{REPO_ID}", timeout=180)
    response.raise_for_status()
    payload = response.json()
    if payload.get("gated") or payload.get("private"):
        raise RuntimeError(f"Dataset unexpectedly gated or private: {REPO_ID}")
    return sorted(
        sibling["rfilename"]
        for sibling in payload.get("siblings", [])
        if sibling.get("rfilename", "").startswith(SOURCE_PREFIX)
        and sibling.get("rfilename", "").endswith(SOURCE_SUFFIX)
    )


def download(endpoint: str, repo_path: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    url = f"{endpoint}/datasets/{REPO_ID}/resolve/main/{quote(repo_path, safe='/')}"
    partial = target.with_suffix(target.suffix + ".part")
    for attempt in range(1, 7):
        headers = {}
        mode = "wb"
        if partial.exists() and partial.stat().st_size:
            headers["Range"] = f"bytes={partial.stat().st_size}-"
            mode = "ab"
        try:
            with requests.get(url, headers=headers, stream=True, timeout=(45, 240)) as response:
                if response.status_code == 200 and mode == "ab":
                    mode = "wb"
                response.raise_for_status()
                with partial.open(mode) as handle:
                    for chunk in response.iter_content(4 * 1024 * 1024):
                        if chunk:
                            handle.write(chunk)
            partial.replace(target)
            return
        except Exception:
            if attempt == 6:
                raise
            time.sleep(attempt * 5)


def scene_to_mesh(path: Path) -> trimesh.Trimesh:
    loaded = trimesh.load(path, force="scene", process=False)
    if not isinstance(loaded, trimesh.Scene):
        mesh = loaded
    else:
        try:
            mesh = loaded.to_geometry()
        except AttributeError:
            dumped = loaded.dump(concatenate=True)
            mesh = dumped if isinstance(dumped, trimesh.Trimesh) else trimesh.util.concatenate(dumped)
    if not isinstance(mesh, trimesh.Trimesh) or len(mesh.vertices) == 0:
        raise ValueError(f"No triangle mesh in {path}")
    mesh.remove_unreferenced_vertices()
    mesh.merge_vertices()
    return mesh


def audit_mesh(path: Path) -> dict[str, object]:
    mesh = scene_to_mesh(path)
    components = mesh.split(only_watertight=False)
    extents = np.asarray(mesh.extents, dtype=float)
    volume = abs(float(mesh.volume))
    surface_area = float(mesh.area)
    valid = bool(
        mesh.is_watertight
        and mesh.is_winding_consistent
        and mesh.is_volume
        and np.isfinite(volume)
        and volume > 1e-12
        and np.isfinite(extents).all()
        and float(extents.min()) > 1e-8
    )
    return {
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "is_volume": bool(mesh.is_volume),
        "connected_components": int(len(components)),
        "volume": volume,
        "surface_area": surface_area,
        "extent_x": float(extents[0]),
        "extent_y": float(extents[1]),
        "extent_z": float(extents[2]),
        "solid_gt_valid": valid,
    }


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    files = repo_files(args.endpoint)[: args.candidate_limit]
    records: list[dict[str, object]] = []
    for index, repo_path in enumerate(files, start=1):
        object_name = repo_path[len(SOURCE_PREFIX) : -len(SOURCE_SUFFIX)]
        target = args.output / "candidates" / object_name / "model.glb"
        record: dict[str, object] = {
            "object_name": object_name,
            "source_repo": REPO_ID,
            "source_path": repo_path,
            "local_path": str(target),
            "excluded_name": any(term in object_name.lower() for term in EXCLUDE_TERMS),
        }
        try:
            if not target.exists():
                download(args.endpoint, repo_path, target)
            record["bytes"] = int(target.stat().st_size)
            record["sha256"] = sha256(target)
            record.update(audit_mesh(target))
            record["status"] = "audited"
        except Exception as error:
            record["status"] = "failed"
            record["error"] = repr(error)
        records.append(record)
        print(
            "AUDIT",
            index,
            len(files),
            object_name,
            record.get("solid_gt_valid"),
            record.get("watertight"),
            record.get("connected_components"),
            flush=True,
        )
        (args.output / "candidate_audit.json").write_text(
            json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    valid = [
        row
        for row in records
        if row.get("solid_gt_valid") and not row.get("excluded_name")
    ]
    valid.sort(
        key=lambda row: (
            int(row.get("connected_components", 999)),
            int(row.get("faces", 0)) > 2_000_000,
            str(row["object_name"]),
        )
    )
    selected = valid[: args.count]
    manifest_path = args.output / "pilot30_manifest.csv"
    fieldnames = [
        "object_id",
        "object_name",
        "source_repo",
        "source_path",
        "mesh_path",
        "mesh_sha256",
        "vertices",
        "faces",
        "connected_components",
        "volume",
        "extent_x",
        "extent_y",
        "extent_z",
    ]
    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for index, row in enumerate(selected, start=1):
            writer.writerow(
                {
                    "object_id": f"gso_{index:03d}",
                    "object_name": row["object_name"],
                    "source_repo": row["source_repo"],
                    "source_path": row["source_path"],
                    "mesh_path": row["local_path"],
                    "mesh_sha256": row["sha256"],
                    "vertices": row["vertices"],
                    "faces": row["faces"],
                    "connected_components": row["connected_components"],
                    "volume": row["volume"],
                    "extent_x": row["extent_x"],
                    "extent_y": row["extent_y"],
                    "extent_z": row["extent_z"],
                }
            )

    summary = {
        "source_repo": REPO_ID,
        "endpoint": args.endpoint,
        "candidates_found": len(files),
        "audited": sum(row.get("status") == "audited" for row in records),
        "solid_gt_valid": sum(bool(row.get("solid_gt_valid")) for row in records),
        "solid_gt_valid_after_name_exclusions": len(valid),
        "selected": len(selected),
        "requested": args.count,
        "gate_passed": len(selected) == args.count,
    }
    (args.output / "dataset_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("SUMMARY", json.dumps(summary, ensure_ascii=False), flush=True)
    return 0 if summary["gate_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
