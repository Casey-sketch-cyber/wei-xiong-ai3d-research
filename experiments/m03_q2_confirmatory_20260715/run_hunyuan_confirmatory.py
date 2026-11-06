from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

import torch
import trimesh
from PIL import Image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=25)
    parser.add_argument("--resolution", type=int, default=384)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--records-name", default="hunyuan21_results.json")
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
    os.chdir(args.repo)
    sys.path.insert(0, str(args.repo / "hy3dshape"))
    sys.path.insert(0, str(args.repo / "hy3dpaint"))
    sys.path.insert(0, str(args.repo))

    try:
        from torchvision_fix import apply_fix

        apply_fix()
    except Exception as error:
        print("torchvision_fix_warning", repr(error), flush=True)

    from hy3dshape.pipelines import Hunyuan3DDiTFlowMatchingPipeline

    with args.manifest.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    jobs = [{**row, "seed": int(row["seed"])} for row in rows]
    if args.limit:
        jobs = jobs[: args.limit]
    if args.shard_count < 1 or not 0 <= args.shard_index < args.shard_count:
        raise ValueError("shard-index must be in [0, shard-count)")
    jobs = jobs[args.shard_index :: args.shard_count]

    records_path = args.work / args.records_name
    primary_path = args.work / "hunyuan21_results.json"
    previous = []
    if primary_path.exists():
        previous.extend(json.loads(primary_path.read_text(encoding="utf-8")))
    if records_path != primary_path and records_path.exists():
        previous.extend(json.loads(records_path.read_text(encoding="utf-8")))
    by_key = {
        (row["job_id"], int(row["seed"])): row for row in previous
    }

    print("Loading Hunyuan3D-2.1 shape pipeline", flush=True)
    pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained("tencent/Hunyuan3D-2.1")

    for index, job in enumerate(jobs, start=1):
        key = (job["job_id"], job["seed"])
        mesh_path = (
            args.work
            / "outputs"
            / "hunyuan21"
            / job["job_id"]
            / f"seed_{job['seed']}"
            / "mesh.ply"
        )
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
            "seed": job["seed"],
            "input_path": job["input_path"],
            "input_sha256": job["input_sha256"],
            "mesh_path": str(mesh_path),
            "status": "started",
            "steps": args.steps,
            "octree_resolution": args.resolution,
        }
        by_key[key] = rec
        atomic_json(records_path, sorted(by_key.values(), key=lambda row: (row["job_id"], row["seed"])))
        print("START", index, len(jobs), key, flush=True)
        try:
            image = Image.open(job["input_path"]).convert("RGBA")
            generator = torch.Generator(device="cuda").manual_seed(job["seed"])
            torch.manual_seed(job["seed"])
            started = time.time()
            with torch.inference_mode():
                mesh = pipeline(
                    image=image,
                    num_inference_steps=args.steps,
                    octree_resolution=args.resolution,
                    generator=generator,
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
            atomic_json(records_path, sorted(by_key.values(), key=lambda row: (row["job_id"], row["seed"])))

    rows = list(by_key.values())
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=args.repo, text=True).strip()
    artifact_suffix = "" if args.records_name == "hunyuan21_results.json" else f"_{args.shard_index}"
    atomic_json(
        args.work / f"hunyuan21_provenance{artifact_suffix}.json",
        {
            "repo": str(args.repo),
            "repo_commit": commit,
            "model": "tencent/Hunyuan3D-2.1",
            "manifest": str(args.manifest),
            "manifest_sha256": sha256(args.manifest),
            "steps": args.steps,
            "octree_resolution": args.resolution,
            "seeds": sorted({int(job["seed"]) for job in jobs}),
            "paired_seed_design": True,
            "shard_count": args.shard_count,
            "shard_index": args.shard_index,
            "records_name": args.records_name,
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
    atomic_json(args.work / f"hunyuan21_summary{artifact_suffix}.json", summary)
    print("SUMMARY", json.dumps(summary), flush=True)
    return 0 if summary["failed"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
