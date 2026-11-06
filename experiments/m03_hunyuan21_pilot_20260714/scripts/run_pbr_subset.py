#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import traceback
from pathlib import Path


STYLES = ("photo", "edge", "flat", "low_detail", "sketch", "watercolor")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260714)
    parser.add_argument("--resolution", type=int, default=512)
    parser.add_argument("--limit", type=int, default=0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sys.path.insert(0, str(args.repo))
    sys.path.insert(0, str(args.repo / "hy3dshape"))
    sys.path.insert(0, str(args.repo / "hy3dpaint"))
    os.chdir(args.repo)

    import torch  # Load PyTorch libraries before the compiled rasterizer extension.
    from utils.torchvision_fix import apply_fix

    apply_fix()
    from hy3dpaint.textureGenPipeline import Hunyuan3DPaintConfig, Hunyuan3DPaintPipeline

    with args.manifest.open("r", encoding="utf-8-sig", newline="") as handle:
        objects = [row for row in csv.DictReader(handle) if row["pbr_selected"].lower() == "true"]
    jobs = [(obj, style) for obj in objects for style in STYLES]
    if args.limit > 0:
        jobs = jobs[: args.limit]

    out_root = args.work / "outputs" / "pbr"
    out_root.mkdir(parents=True, exist_ok=True)
    results_path = args.work / "pbr_results.json"
    previous = json.loads(results_path.read_text(encoding="utf-8")) if results_path.exists() else []
    by_key = {(row["uid"], row["style"]): row for row in previous}

    print("loading_paint_pipeline", flush=True)
    started = time.time()
    config = Hunyuan3DPaintConfig(max_num_view=6, resolution=args.resolution)
    config.realesrgan_ckpt_path = str(
        args.repo / "hy3dpaint" / "ckpt" / "RealESRGAN_x4plus.pth"
    )
    pipeline = Hunyuan3DPaintPipeline(config)
    print("paint_pipeline_loaded_seconds", round(time.time() - started, 2), flush=True)

    for index, (obj, style) in enumerate(jobs, start=1):
        key = (obj["uid"], style)
        shape_path = (
            args.work
            / "outputs"
            / "shape"
            / obj["uid"]
            / style
            / f"seed_{args.seed}"
            / "shape.glb"
        )
        image_path = args.dataset / obj["uid"] / "variants" / f"{style}.png"
        item_out = out_root / obj["uid"] / style
        item_out.mkdir(parents=True, exist_ok=True)
        output_obj_path = item_out / "textured.obj"
        output_glb_path = item_out / "textured.glb"
        if key in by_key and by_key[key].get("status") == "success" and output_glb_path.exists():
            print("SKIP", index, len(jobs), key, flush=True)
            continue
        if not shape_path.exists():
            raise FileNotFoundError(shape_path)
        rec = {
            "uid": obj["uid"],
            "name": obj["name"],
            "style": style,
            "seed": args.seed,
            "shape_path": str(shape_path),
            "image_path": str(image_path),
            "output_obj": str(output_obj_path),
            "output_glb": str(output_glb_path),
            "status": "started",
            "seconds": None,
            "error": "",
        }
        by_key[key] = rec
        print("START", index, len(jobs), key, flush=True)
        try:
            item_started = time.time()
            pipeline(
                mesh_path=str(shape_path),
                image_path=str(image_path),
                output_mesh_path=str(output_obj_path),
                use_remesh=True,
                save_glb=True,
            )
            if not output_glb_path.exists():
                raise FileNotFoundError(f"Paint pipeline did not create {output_glb_path}")
            rec["status"] = "success"
            rec["seconds"] = round(time.time() - item_started, 3)
            rec["output_bytes"] = output_glb_path.stat().st_size if output_glb_path.exists() else 0
            print("DONE", index, len(jobs), key, rec["seconds"], flush=True)
        except Exception as exc:
            rec["status"] = "failed"
            rec["error"] = repr(exc)
            (item_out / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
            print("FAILED", index, len(jobs), key, repr(exc), flush=True)
        finally:
            ordered = sorted(by_key.values(), key=lambda row: (row["uid"], row["style"]))
            results_path.write_text(
                json.dumps(ordered, ensure_ascii=False, indent=2), encoding="utf-8"
            )

    ordered = sorted(by_key.values(), key=lambda row: (row["uid"], row["style"]))
    summary = {
        "jobs_requested": len(jobs),
        "success": sum(row.get("status") == "success" for row in ordered),
        "failed": sum(row.get("status") == "failed" for row in ordered),
        "texture_resolution": args.resolution,
        "official_pipeline": "Hunyuan3DPaintPipeline",
        "official_remesh": True,
        "torch_version": torch.__version__,
    }
    (args.work / "pbr_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("SUMMARY", json.dumps(summary, ensure_ascii=False), flush=True)
    return 0 if summary["failed"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
