from __future__ import annotations

import argparse
import csv
import gc
import hashlib
import json
import os
import subprocess
import time
import traceback
from pathlib import Path


os.environ.setdefault("ATTN_BACKEND", "flash_attn")
os.environ.setdefault("SPARSE_ATTN_BACKEND", "flash_attn")
os.environ.setdefault("SPCONV_ALGO", "native")

import torch
import trimesh
from PIL import Image
from trellis.pipelines import TrellisImageTo3DPipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--model", default="microsoft/TRELLIS-image-large")
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
        while chunk := handle.read(4 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def save_records(path: Path, records: dict[tuple[str, int], dict[str, object]]) -> None:
    atomic_json(
        path,
        sorted(records.values(), key=lambda row: (str(row["job_id"]), int(row["seed"]))),
    )


def main() -> int:
    args = parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    os.chdir(args.repo)
    with args.manifest.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    jobs = [{**row, "seed": int(row["seed"])} for row in rows]
    if args.limit:
        jobs = jobs[: args.limit]

    records_path = args.work / "trellis_results.json"
    previous = json.loads(records_path.read_text(encoding="utf-8")) if records_path.exists() else []
    by_key = {(str(row["job_id"]), int(row["seed"])): row for row in previous}

    load_started = time.time()
    pipeline = TrellisImageTo3DPipeline.from_pretrained(args.model)
    removed_decoders = []
    for key in ("slat_decoder_gs", "slat_decoder_rf"):
        if key in pipeline.models:
            removed_decoders.append(key)
            del pipeline.models[key]
    pipeline.cuda()
    model_load_seconds = time.time() - load_started

    for index, job in enumerate(jobs, start=1):
        key = (job["job_id"], job["seed"])
        mesh_path = (
            args.work
            / "outputs"
            / "trellis"
            / job["job_id"]
            / f"seed_{job['seed']}"
            / "mesh.obj"
        )
        previous_record = by_key.get(key)
        if (
            previous_record is not None
            and previous_record.get("status") == "success"
            and mesh_path.exists()
        ):
            print("SKIP", index, len(jobs), key, flush=True)
            continue

        mesh_path.parent.mkdir(parents=True, exist_ok=True)
        record: dict[str, object] = {
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
        }
        by_key[key] = record
        save_records(records_path, by_key)
        print("START", index, len(jobs), key, flush=True)
        try:
            image = Image.open(job["input_path"]).convert("RGBA")
            torch.cuda.reset_peak_memory_stats()
            started = time.time()
            outputs = pipeline.run(image, seed=job["seed"], formats=["mesh"])
            torch.cuda.synchronize()
            mesh = outputs["mesh"][0]
            if not mesh.success:
                raise RuntimeError("TRELLIS mesh decoder returned an empty mesh")
            vertices = mesh.vertices.detach().float().cpu().numpy()
            faces = mesh.faces.detach().long().cpu().numpy()
            exported = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
            exported.export(mesh_path, file_type="obj")
            record.update(
                {
                    "status": "success",
                    "seconds": round(time.time() - started, 3),
                    "mesh_sha256": file_sha256(mesh_path),
                    "vertices": int(len(vertices)),
                    "faces": int(len(faces)),
                    "watertight": bool(exported.is_watertight),
                    "winding_consistent": bool(exported.is_winding_consistent),
                    "peak_gpu_gib": float(torch.cuda.max_memory_allocated() / 1024**3),
                }
            )
            print("DONE", index, len(jobs), key, record["seconds"], flush=True)
            del image, outputs, mesh, vertices, faces, exported
        except Exception as error:
            record["status"] = "failed"
            record["error"] = repr(error)
            (mesh_path.parent / "error.txt").write_text(
                traceback.format_exc(), encoding="utf-8"
            )
            print("FAILED", index, len(jobs), key, repr(error), flush=True)
        finally:
            save_records(records_path, by_key)
            gc.collect()
            if index % 20 == 0:
                torch.cuda.empty_cache()

    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=args.repo, text=True
    ).strip()
    atomic_json(
        args.work / "trellis_provenance.json",
        {
            "repo": str(args.repo),
            "repo_commit": commit,
            "model": args.model,
            "manifest": str(args.manifest),
            "manifest_sha256": file_sha256(args.manifest),
            "jobs_requested": len(jobs),
            "seeds": sorted({int(job["seed"]) for job in jobs}),
            "paired_seed_design": True,
            "formats": ["mesh"],
            "removed_unused_decoders": removed_decoders,
            "sampler_parameters": {
                "sparse_structure": pipeline.sparse_structure_sampler_params,
                "slat": pipeline.slat_sampler_params,
            },
            "attention_backend": os.environ["ATTN_BACKEND"],
            "spconv_algorithm": os.environ["SPCONV_ALGO"],
            "model_load_seconds": model_load_seconds,
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
            "gpu": torch.cuda.get_device_name(0),
        },
    )
    relevant = [by_key[(job["job_id"], job["seed"])] for job in jobs]
    summary = {
        "jobs_requested": len(jobs),
        "success": sum(row.get("status") == "success" for row in relevant),
        "failed": sum(row.get("status") == "failed" for row in relevant),
    }
    atomic_json(args.work / "trellis_summary.json", summary)
    print("SUMMARY", json.dumps(summary), flush=True)
    return 0 if summary["failed"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
