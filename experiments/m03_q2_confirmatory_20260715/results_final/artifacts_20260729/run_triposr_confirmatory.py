from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import time
import traceback
from pathlib import Path

import torch
import trimesh
from PIL import Image
from tsr.system import TSR


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--mc-resolution", type=int, default=128)
    parser.add_argument("--chunk-size", type=int, default=4096)
    parser.add_argument("--limit", type=int, default=0)
    return parser.parse_args()


def atomic_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    args = parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    with args.manifest.open("r", encoding="utf-8-sig", newline="") as handle:
        jobs = list(csv.DictReader(handle))
    if args.limit:
        jobs = jobs[: args.limit]

    records_path = args.work / "triposr_results.json"
    previous = json.loads(records_path.read_text(encoding="utf-8")) if records_path.exists() else []
    by_key = {row["job_id"]: row for row in previous}

    model = TSR.from_pretrained(
        "stabilityai/TripoSR", config_name="config.yaml", weight_name="model.ckpt"
    )
    model.renderer.set_chunk_size(args.chunk_size)
    model.to("cuda")
    model.eval()

    for index, job in enumerate(jobs, start=1):
        key = job["job_id"]
        mesh_path = args.work / "outputs" / "triposr" / key / "mesh.ply"
        if key in by_key and by_key[key].get("status") == "success" and mesh_path.exists():
            print("SKIP", index, len(jobs), key, flush=True)
            continue
        mesh_path.parent.mkdir(parents=True, exist_ok=True)
        rec = {
            "job_id": job["job_id"],
            "object_id": job["object_id"],
            "object_name": job["object_name"],
            "split": job["split"],
            "view_id": job["view_id"],
            "style": job["style"],
            "severity": job["severity"],
            "seed": None,
            "input_path": job["input_path"],
            "input_sha256": job["input_sha256"],
            "mesh_path": str(mesh_path),
            "status": "started",
        }
        by_key[key] = rec
        atomic_json(records_path, sorted(by_key.values(), key=lambda row: row["job_id"]))
        print("START", index, len(jobs), key, flush=True)
        try:
            image = Image.open(job["input_path"]).convert("RGB")
            started = time.time()
            with torch.inference_mode():
                scene_codes = model([image], device="cuda")
                mesh = model.extract_mesh(
                    scene_codes, has_vertex_color=False, resolution=args.mc_resolution
                )[0]
            mesh.export(mesh_path)
            torch.cuda.synchronize()
            loaded = trimesh.load(mesh_path, force="mesh", process=False)
            rec.update(
                {
                    "status": "success",
                    "seconds": round(time.time() - started, 3),
                    "mesh_sha256": sha256(mesh_path),
                    "vertices": int(len(loaded.vertices)),
                    "faces": int(len(loaded.faces)),
                    "watertight": bool(loaded.is_watertight),
                }
            )
            print("DONE", index, len(jobs), key, rec["seconds"], flush=True)
        except Exception as error:
            rec["status"] = "failed"
            rec["error"] = repr(error)
            (mesh_path.parent / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
            print("FAILED", index, len(jobs), key, repr(error), flush=True)
        finally:
            atomic_json(records_path, sorted(by_key.values(), key=lambda row: row["job_id"]))

    rows = list(by_key.values())
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=args.repo, text=True).strip()
    atomic_json(
        args.work / "triposr_provenance.json",
        {
            "repo": str(args.repo),
            "repo_commit": commit,
            "model": "stabilityai/TripoSR",
            "manifest": str(args.manifest),
            "manifest_sha256": sha256(args.manifest),
            "mc_resolution": args.mc_resolution,
            "chunk_size": args.chunk_size,
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
            "gpu": torch.cuda.get_device_name(0),
        },
    )
    summary = {
        "jobs_requested": len(jobs),
        "records": len(rows),
        "success": sum(row.get("status") == "success" for row in rows),
        "failed": sum(row.get("status") == "failed" for row in rows),
    }
    atomic_json(args.work / "triposr_summary.json", summary)
    print("SUMMARY", json.dumps(summary), flush=True)
    return 0 if summary["failed"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
