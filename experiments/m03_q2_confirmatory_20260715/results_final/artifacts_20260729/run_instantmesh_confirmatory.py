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

import numpy as np
import torch
from diffusers import DiffusionPipeline, EulerAncestralDiscreteScheduler
from einops import rearrange
from huggingface_hub import hf_hub_download
from omegaconf import OmegaConf
from PIL import Image
from pytorch_lightning import seed_everything
from torchvision.transforms import v2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--stage", choices=("multiview", "mesh", "all"), default="all")
    parser.add_argument("--steps", type=int, default=75)
    parser.add_argument("--limit", type=int, default=0)
    return parser.parse_args()


def atomic_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_commit(repo: Path) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo, text=True
    ).strip()


def load_jobs(args: argparse.Namespace) -> list[dict]:
    with args.manifest.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    jobs = [{**row, "seed": int(row["seed"])} for row in rows]
    return jobs[: args.limit] if args.limit else jobs


def load_records(path: Path) -> dict[tuple[str, int], dict]:
    if not path.exists():
        return {}
    rows = json.loads(path.read_text(encoding="utf-8"))
    return {
        (row["job_id"], int(row["seed"])): row for row in rows
    }


def save_records(path: Path, by_key: dict[tuple[str, int], dict]) -> None:
    rows = sorted(
        by_key.values(), key=lambda row: (row["job_id"], row["seed"])
    )
    atomic_json(path, rows)


def output_paths(work: Path, job: dict) -> tuple[Path, Path]:
    root = (
        work
        / "outputs"
        / "instantmesh"
        / job["job_id"]
        / f"seed_{job['seed']}"
    )
    return root / "multiview.png", root / "mesh.obj"


def run_multiview(
    args: argparse.Namespace,
    config: OmegaConf,
    jobs: list[dict],
    records_path: Path,
    by_key: dict[tuple[str, int], dict],
) -> None:
    print("Loading Zero123++ diffusion pipeline", flush=True)
    pipeline = DiffusionPipeline.from_pretrained(
        "sudo-ai/zero123plus-v1.2",
        custom_pipeline="zero123plus",
        torch_dtype=torch.float16,
    )
    pipeline.scheduler = EulerAncestralDiscreteScheduler.from_config(
        pipeline.scheduler.config, timestep_spacing="trailing"
    )
    unet_path = Path(config.infer_config.unet_path)
    if not unet_path.exists():
        unet_path = Path(
            hf_hub_download(
                repo_id="TencentARC/InstantMesh",
                filename="diffusion_pytorch_model.bin",
                repo_type="model",
            )
        )
    pipeline.unet.load_state_dict(torch.load(unet_path, map_location="cpu"), strict=True)
    pipeline = pipeline.to("cuda")

    for index, job in enumerate(jobs, start=1):
        key = (job["job_id"], job["seed"])
        multiview_path, mesh_path = output_paths(args.work, job)
        rec = by_key.setdefault(
            key,
            {
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
                "multiview_path": str(multiview_path),
                "mesh_path": str(mesh_path),
            },
        )
        if rec.get("multiview_status") == "success" and multiview_path.exists():
            print("SKIP_MV", index, len(jobs), key, flush=True)
            continue
        multiview_path.parent.mkdir(parents=True, exist_ok=True)
        rec["multiview_status"] = "started"
        save_records(records_path, by_key)
        print("START_MV", index, len(jobs), key, flush=True)
        try:
            seed_everything(job["seed"], workers=True)
            generator = torch.Generator(device="cuda").manual_seed(job["seed"])
            image = Image.open(job["input_path"]).convert("RGBA")
            started = time.time()
            with torch.inference_mode():
                output = pipeline(
                    image,
                    num_inference_steps=args.steps,
                    generator=generator,
                ).images[0]
            torch.cuda.synchronize()
            output.save(multiview_path)
            rec.update(
                {
                    "multiview_status": "success",
                    "multiview_seconds": round(time.time() - started, 3),
                    "multiview_sha256": file_sha256(multiview_path),
                    "diffusion_steps": args.steps,
                }
            )
            print("DONE_MV", index, len(jobs), key, rec["multiview_seconds"], flush=True)
        except Exception as error:
            rec["multiview_status"] = "failed"
            rec["multiview_error"] = repr(error)
            (multiview_path.parent / "multiview_error.txt").write_text(
                traceback.format_exc(), encoding="utf-8"
            )
            print("FAILED_MV", index, len(jobs), key, repr(error), flush=True)
        finally:
            save_records(records_path, by_key)

    del pipeline
    torch.cuda.empty_cache()


def run_mesh(
    args: argparse.Namespace,
    config: OmegaConf,
    config_name: str,
    jobs: list[dict],
    records_path: Path,
    by_key: dict[tuple[str, int], dict],
) -> None:
    from src.utils.camera_util import get_zero123plus_input_cameras
    from src.utils.mesh_util import save_obj
    from src.utils.train_util import instantiate_from_config

    print("Loading InstantMesh reconstruction model", flush=True)
    model = instantiate_from_config(config.model_config)
    model_path = Path(config.infer_config.model_path)
    if not model_path.exists():
        model_path = Path(
            hf_hub_download(
                repo_id="TencentARC/InstantMesh",
                filename=f"{config_name.replace('-', '_')}.ckpt",
                repo_type="model",
            )
        )
    state_dict = torch.load(model_path, map_location="cpu")["state_dict"]
    state_dict = {
        key[14:]: value
        for key, value in state_dict.items()
        if key.startswith("lrm_generator.")
    }
    model.load_state_dict(state_dict, strict=True)
    model = model.to("cuda")
    model.init_flexicubes_geometry(torch.device("cuda"), fovy=30.0)
    model = model.eval()
    cameras = get_zero123plus_input_cameras(batch_size=1, radius=4.0).to("cuda")

    for index, job in enumerate(jobs, start=1):
        key = (job["job_id"], job["seed"])
        multiview_path, mesh_path = output_paths(args.work, job)
        rec = by_key.setdefault(
            key,
            {
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
                "multiview_path": str(multiview_path),
                "mesh_path": str(mesh_path),
            },
        )
        if rec.get("mesh_status") == "success" and mesh_path.exists():
            print("SKIP_MESH", index, len(jobs), key, flush=True)
            continue
        if not multiview_path.exists():
            rec["mesh_status"] = "blocked_missing_multiview"
            save_records(records_path, by_key)
            continue
        rec["mesh_status"] = "started"
        save_records(records_path, by_key)
        print("START_MESH", index, len(jobs), key, flush=True)
        try:
            image = np.asarray(Image.open(multiview_path).convert("RGB"), dtype=np.float32) / 255.0
            images = torch.from_numpy(image).permute(2, 0, 1).contiguous().float()
            images = rearrange(images, "c (n h) (m w) -> (n m) c h w", n=3, m=2)
            images = images.unsqueeze(0).to("cuda")
            images = v2.functional.resize(
                images, 320, interpolation=3, antialias=True
            ).clamp(0, 1)
            started = time.time()
            with torch.inference_mode():
                planes = model.forward_planes(images, cameras)
                vertices, faces, vertex_colors = model.extract_mesh(
                    planes, use_texture_map=False, **config.infer_config
                )
            save_obj(vertices, faces, vertex_colors, mesh_path)
            torch.cuda.synchronize()
            rec.update(
                {
                    "mesh_status": "success",
                    "mesh_seconds": round(time.time() - started, 3),
                    "mesh_sha256": file_sha256(mesh_path),
                    "vertices": int(vertices.shape[0]),
                    "faces": int(faces.shape[0]),
                }
            )
            print("DONE_MESH", index, len(jobs), key, rec["mesh_seconds"], flush=True)
            del images, planes, vertices, faces, vertex_colors
        except Exception as error:
            rec["mesh_status"] = "failed"
            rec["mesh_error"] = repr(error)
            (mesh_path.parent / "mesh_error.txt").write_text(
                traceback.format_exc(), encoding="utf-8"
            )
            print("FAILED_MESH", index, len(jobs), key, repr(error), flush=True)
        finally:
            save_records(records_path, by_key)


def main() -> int:
    args = parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    os.chdir(args.repo)
    sys.path.insert(0, str(args.repo))
    config_path = args.repo / "configs" / "instant-mesh-large.yaml"
    config = OmegaConf.load(config_path)
    config_name = config_path.stem
    jobs = load_jobs(args)
    records_path = args.work / "instantmesh_results.json"
    by_key = load_records(records_path)

    atomic_json(
        args.work / "instantmesh_provenance.json",
        {
            "repo": str(args.repo),
            "repo_commit": git_commit(args.repo),
            "model": "TencentARC/InstantMesh",
            "multiview_model": "sudo-ai/zero123plus-v1.2",
            "config": str(config_path),
            "manifest": str(args.manifest),
            "manifest_sha256": file_sha256(args.manifest),
            "diffusion_steps": args.steps,
            "seeds": sorted({int(job["seed"]) for job in jobs}),
            "paired_seed_design": True,
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
            "gpu": torch.cuda.get_device_name(0),
        },
    )

    if args.stage in ("multiview", "all"):
        run_multiview(args, config, jobs, records_path, by_key)
    if args.stage in ("mesh", "all"):
        run_mesh(args, config, config_name, jobs, records_path, by_key)

    rows = list(by_key.values())
    summary = {
        "jobs_requested": len(jobs),
        "records": len(rows),
        "multiview_success": sum(row.get("multiview_status") == "success" for row in rows),
        "mesh_success": sum(row.get("mesh_status") == "success" for row in rows),
        "multiview_failed": sum(row.get("multiview_status") == "failed" for row in rows),
        "mesh_failed": sum(row.get("mesh_status") == "failed" for row in rows),
    }
    atomic_json(args.work / "instantmesh_summary.json", summary)
    print("SUMMARY", json.dumps(summary), flush=True)
    return 0 if summary["multiview_failed"] == 0 and summary["mesh_failed"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
