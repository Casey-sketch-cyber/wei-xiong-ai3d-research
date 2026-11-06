from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path


os.environ.setdefault("ATTN_BACKEND", "xformers")
os.environ.setdefault("SPARSE_ATTN_BACKEND", "xformers")
os.environ.setdefault("SPCONV_ALGO", "native")

import numpy as np
import torch
import trimesh
from PIL import Image
from trellis.pipelines import TrellisImageTo3DPipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default="microsoft/TRELLIS-image-large")
    parser.add_argument("--seed", type=int, default=20260715)
    return parser.parse_args()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(4 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    started = time.time()
    pipeline = TrellisImageTo3DPipeline.from_pretrained(args.model)
    loaded_seconds = time.time() - started

    removed_decoders = []
    for key in ("slat_decoder_gs", "slat_decoder_rf"):
        if key in pipeline.models:
            removed_decoders.append(key)
            del pipeline.models[key]
    pipeline.cuda()

    image = Image.open(args.image).convert("RGBA")
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    inference_started = time.time()
    outputs = pipeline.run(image, seed=args.seed, formats=["mesh"])
    inference_seconds = time.time() - inference_started
    mesh = outputs["mesh"][0]
    if not mesh.success:
        raise RuntimeError("TRELLIS mesh decoder returned an empty mesh")

    vertices = mesh.vertices.detach().float().cpu().numpy()
    faces = mesh.faces.detach().long().cpu().numpy()
    target = args.output / "trellis_smoke.obj"
    exported = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    exported.export(target, file_type="obj")

    provenance = {
        "model": args.model,
        "seed": args.seed,
        "image": str(args.image),
        "image_sha256": file_sha256(args.image),
        "mesh_path": str(target),
        "mesh_sha256": file_sha256(target),
        "vertices": int(len(vertices)),
        "faces": int(len(faces)),
        "watertight": bool(exported.is_watertight),
        "winding_consistent": bool(exported.is_winding_consistent),
        "components": int(len(exported.split(only_watertight=False))),
        "load_seconds": loaded_seconds,
        "inference_seconds": inference_seconds,
        "total_seconds": time.time() - started,
        "peak_gpu_gib": float(torch.cuda.max_memory_allocated() / 1024**3),
        "torch": torch.__version__,
        "cuda": torch.version.cuda,
        "device": torch.cuda.get_device_name(0),
        "attention_backend": os.environ["ATTN_BACKEND"],
        "spconv_algorithm": os.environ["SPCONV_ALGO"],
        "formats": ["mesh"],
        "removed_unused_decoders": removed_decoders,
        "sampler_parameters": {
            "sparse_structure": pipeline.sparse_structure_sampler_params,
            "slat": pipeline.slat_sampler_params,
        },
    }
    (args.output / "trellis_smoke_provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("TRELLIS_SMOKE", json.dumps(provenance, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
