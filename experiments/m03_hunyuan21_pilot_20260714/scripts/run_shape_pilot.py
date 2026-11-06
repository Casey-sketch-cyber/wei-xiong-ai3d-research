#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import sys
import time
import traceback
from pathlib import Path

import torch
from PIL import Image


STYLES = ("photo", "edge", "flat", "low_detail", "sketch", "watercolor")
DEFAULT_SEEDS = (20260714, 3407)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=25)
    parser.add_argument("--resolution", type=int, default=384)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(DEFAULT_SEEDS))
    parser.add_argument("--limit", type=int, default=0)
    return parser.parse_args()


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    args = parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    out_root = args.work / "outputs" / "shape"
    out_root.mkdir(parents=True, exist_ok=True)
    records_path = args.work / "shape_results.json"

    sys.path.insert(0, str(args.repo / "hy3dshape"))
    sys.path.insert(0, str(args.repo / "hy3dpaint"))
    os.chdir(args.repo)

    try:
        from torchvision_fix import apply_fix

        apply_fix()
    except Exception as exc:
        print("torchvision_fix_warning", repr(exc), flush=True)

    from hy3dshape.pipelines import Hunyuan3DDiTFlowMatchingPipeline

    try:
        from hy3dshape.rembg import BackgroundRemover
    except Exception as exc:
        BackgroundRemover = None
        print("rembg_import_warning", repr(exc), flush=True)

    print("python", sys.version, flush=True)
    print("torch", torch.__version__, torch.version.cuda, flush=True)
    print("gpu", torch.cuda.get_device_name(0), flush=True)
    print("loading_shape_pipeline", flush=True)
    load_started = time.time()
    pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
        "tencent/Hunyuan3D-2.1"
    )
    print("pipeline_loaded_seconds", round(time.time() - load_started, 2), flush=True)

    remover = None
    if BackgroundRemover is not None:
        try:
            remover = BackgroundRemover()
            print("background_remover_ready", flush=True)
        except Exception as exc:
            print("background_remover_failed", repr(exc), flush=True)

    previous: list[dict] = []
    if records_path.exists():
        previous = json.loads(records_path.read_text(encoding="utf-8"))
    by_key = {
        (row["uid"], row["style"], int(row["seed"])): row for row in previous
    }

    jobs = []
    for obj in load_rows(args.manifest):
        for style in STYLES:
            input_path = args.dataset / obj["uid"] / "variants" / f"{style}.png"
            if not input_path.exists():
                raise FileNotFoundError(input_path)
            for seed in args.seeds:
                jobs.append((obj, style, seed, input_path))
    if args.limit > 0:
        jobs = jobs[: args.limit]

    for index, (obj, style, seed, input_path) in enumerate(jobs, start=1):
        key = (obj["uid"], style, int(seed))
        item_out = out_root / obj["uid"] / style / f"seed_{seed}"
        item_out.mkdir(parents=True, exist_ok=True)
        shape_path = item_out / "shape.glb"
        if key in by_key and by_key[key].get("status") == "success" and shape_path.exists():
            print("SKIP", index, len(jobs), key, flush=True)
            continue

        rec = {
            "uid": obj["uid"],
            "name": obj["name"],
            "stratum": obj["stratum"],
            "style": style,
            "seed": int(seed),
            "input_path": str(input_path),
            "output_glb": str(shape_path),
            "steps": args.steps,
            "octree_resolution": args.resolution,
            "status": "started",
            "seconds": None,
            "error": "",
        }
        by_key[key] = rec
        print("START", index, len(jobs), key, flush=True)
        try:
            image = Image.open(input_path).convert("RGBA")
            shutil.copy2(input_path, item_out / "input.png")
            if remover is not None:
                try:
                    image = remover(image)
                    image.save(item_out / "input_rembg.png")
                    rec["background_removal"] = "official_hunyuan"
                except Exception as exc:
                    rec["background_removal"] = "failed_using_rgba"
                    rec["background_removal_error"] = repr(exc)
            else:
                rec["background_removal"] = "unavailable_using_rgba"

            generator = torch.Generator(device="cuda").manual_seed(int(seed))
            torch.manual_seed(int(seed))
            started = time.time()
            mesh = pipeline(
                image=image,
                num_inference_steps=args.steps,
                octree_resolution=args.resolution,
                generator=generator,
            )[0]
            mesh.export(shape_path)
            rec.update(
                {
                    "status": "success",
                    "seconds": round(time.time() - started, 3),
                    "vertices": int(len(mesh.vertices)),
                    "faces": int(len(mesh.faces)),
                    "watertight": bool(mesh.is_watertight),
                    "volume": abs(float(mesh.volume)) if mesh.is_watertight else None,
                    "extents": [float(value) for value in mesh.extents],
                }
            )
            print("DONE", index, len(jobs), key, rec["seconds"], flush=True)
        except Exception as exc:
            rec["status"] = "failed"
            rec["error"] = repr(exc)
            (item_out / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
            print("FAILED", index, len(jobs), key, repr(exc), flush=True)
        finally:
            ordered = sorted(by_key.values(), key=lambda row: (row["uid"], row["style"], row["seed"]))
            records_path.write_text(
                json.dumps(ordered, ensure_ascii=False, indent=2), encoding="utf-8"
            )

    ordered = sorted(by_key.values(), key=lambda row: (row["uid"], row["style"], row["seed"]))
    summary = {
        "model": "tencent/Hunyuan3D-2.1",
        "jobs_requested": len(jobs),
        "records": len(ordered),
        "success": sum(row.get("status") == "success" for row in ordered),
        "failed": sum(row.get("status") == "failed" for row in ordered),
        "steps": args.steps,
        "octree_resolution": args.resolution,
        "seeds": list(args.seeds),
    }
    (args.work / "shape_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("SUMMARY", json.dumps(summary, ensure_ascii=False), flush=True)
    return 0 if summary["failed"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())

