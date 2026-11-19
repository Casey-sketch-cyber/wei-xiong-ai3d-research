"""PR #5 follow-up with frozen sensitivity inputs and unresized native crops."""
import argparse
import csv
import io
import json
import shutil
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image

from run_pilot import SIZE, STRATA, model_output, read_json, run, save_png, sha256, smoke, write_json

NATIVE_SEED = 20261119
PAIRED_SEED = 2026
NATIVE_WORKS = 4
SENSITIVITY_MODELS = ("sdxl_1024", "sdxl_empty")
NATIVE_MODELS = ("lama", "sdxl", "mat", "powerpaint")


def prepared_dirs(run_dir):
    for part in ("originals", "masks"):
        (run_dir / part).mkdir(parents=True, exist_ok=True)


def freeze_sensitivity(baseline, run_dir):
    source_plan = baseline / "prepared.json"
    source_sha = sha256(source_plan)
    lock = run_dir / "prepared.json"
    if lock.is_file():
        if read_json(lock)["baseline_prepared_sha256"] != source_sha:
            raise ValueError("Sensitivity directory already uses another baseline")
        return
    cases = read_json(source_plan)["cases"]
    if len(cases) != 60:
        raise ValueError("Expected all 60 frozen baseline cases")
    prepared_dirs(run_dir)
    for case in cases:
        name = case["case_id"] + ".png"
        source = baseline / "originals" / name
        if sha256(source) != case["crop_sha256"]:
            raise ValueError(f"Baseline crop mismatch: {name}")
        shutil.copyfile(source, run_dir / "originals" / name)
    masks = {case["mask_file"]: case["mask_sha256"] for case in cases}
    for name, digest in masks.items():
        source = baseline / "masks" / name
        if sha256(source) != digest:
            raise ValueError(f"Baseline mask mismatch: {name}")
        shutil.copyfile(source, run_dir / "masks" / name)
    write_json(lock, {"protocol": "sensitivity-v1", "baseline_prepared_sha256": source_sha,
                      "seed": PAIRED_SEED, "cases": cases})
    print(f"Copied and checked {len(cases)} frozen reference crops", flush=True)


def cma_original(artwork, data_dir, baseline_source_dir):
    from prepare_artworks import API, atomic_write, fetch

    object_id = artwork["artwork_id"]
    record = json.loads(fetch(f"{API}{int(object_id.removeprefix('cma-'))}", 4_000_000))["data"]
    if record["share_license_status"] != "CC0":
        raise ValueError(f"CC0 status changed for {object_id}")
    full = record.get("images", {}).get("full", {}).get("url")
    if full:
        parts = urllib.parse.urlparse(full)
        if parts.scheme != "https" or parts.hostname not in (
            "openaccess-cdn.clevelandart.org", "www.clevelandart.org", "clevelandart.org"
        ):
            raise ValueError(f"Unexpected full-image endpoint for {object_id}")
        destination = data_dir / f"{object_id}-full.image"
        try:
            if not destination.exists():
                payload = fetch(full, 240_000_000)
                with Image.open(io.BytesIO(payload)) as image:
                    if min(image.size) < SIZE:
                        raise ValueError("Full image is smaller than a native crop")
                    image.verify()
                atomic_write(destination, payload)
            return destination, full, "full"
        except (OSError, ValueError) as error:
            print(f"{object_id}: full rendition unavailable ({type(error).__name__})", flush=True)
    source = (baseline_source_dir / artwork["image_path"]).resolve()
    if not source.is_relative_to(baseline_source_dir.resolve()):
        raise ValueError(f"Invalid baseline image path for {object_id}")
    return source, artwork["image_url"], "baseline_rendition"


def prepare_native(manifest, data_dir, run_dir):
    from patch_design import MASK_AREAS, MASK_FAMILIES, design_mask, native_crop

    lock = run_dir / "prepared.json"
    source_sha = sha256(manifest)
    if lock.is_file():
        if read_json(lock)["manifest_sha256"] != source_sha:
            raise ValueError("Native directory already uses another manifest")
        return
    prepared_dirs(run_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    with manifest.open(encoding="utf-8-sig", newline="") as stream:
        source_works = list(csv.DictReader(stream))
    rng = np.random.default_rng(NATIVE_SEED)
    selected = []
    for index, group in enumerate(STRATA):
        works = sorted((row for row in source_works if row["stratum"] == group),
                       key=lambda row: row["artwork_id"])
        if len(works) != 15 or any(row["rights"] != "CC0" for row in works):
            raise ValueError(f"Malformed source stratum: {group}")
        selected.extend((index, slot, works[position])
                        for slot, position in enumerate(rng.permutation(len(works))[:NATIVE_WORKS]))
    if len({art["artwork_id"] for _, _, art in selected}) != 16:
        raise ValueError("Native sample must have 16 unique works")

    mask_records = {}
    for slot in range(NATIVE_WORKS):
        for family_index, family in enumerate(MASK_FAMILIES):
            for area_index, area in enumerate(MASK_AREAS):
                seed = NATIVE_SEED + slot * 100 + family_index * 10 + area_index
                mask = design_mask(family, area, seed)
                name = f"mask_{slot:02}_{family}_{int(100 * area):02}.png"
                path = run_dir / "masks" / name
                save_png(path, mask.astype(np.uint8) * 255)
                mask_records[(slot, family, area)] = (name, sha256(path), int(mask.sum()), seed)

    cases = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        sources = list(pool.map(
            lambda entry: cma_original(entry[2], data_dir, manifest.parent), selected
        ))
    for (group_index, slot, artwork), (source, url, rendition) in zip(selected, sources):
        crop_seed = NATIVE_SEED + 1000 + group_index * 100 + slot
        pixels, (left, top) = native_crop(source, crop_seed)
        source_hash = sha256(source)
        with Image.open(source) as image:
            image_size = list(image.size)
        for family in MASK_FAMILIES:
            for area in MASK_AREAS:
                mask_file, mask_hash, count, seed = mask_records[(slot, family, area)]
                case_id = f"{artwork['stratum']}_{slot:02}_{family}_{int(100 * area):02}"
                original = run_dir / "originals" / f"{case_id}.png"
                save_png(original, pixels)
                cases.append({
                    **artwork, "case_id": case_id, "mask_file": mask_file,
                    "family": family, "target_area": area, "mask_pixels": count, "mask_seed": seed,
                    "crop_left_top": [left, top], "crop_seed": crop_seed,
                    "source_size": image_size, "source_rendition": rendition, "source_url_image": url,
                    "source_image_sha256": source_hash, "crop_sha256": sha256(original),
                    "mask_sha256": mask_hash,
                })
        print(f"Prepared native crop: {artwork['artwork_id']} ({rendition})", flush=True)
    write_json(lock, {"protocol": "native-v2", "manifest_sha256": source_sha,
                      "seed": PAIRED_SEED, "cases": cases})
    print(f"Prepared {len(cases)} conditions across {len(selected)} artworks", flush=True)


def followup_model(name, device, models_dir):
    from models import load_model

    if name == "sdxl_empty":
        return load_model("sdxl", device, models_dir, prompt="")
    if name == "sdxl_1024":
        model = load_model("sdxl", device, models_dir)

        def upscale_inpaint(damaged, mask, seed):
            image = Image.fromarray(damaged)
            high_image = np.array(image.resize((1024, 1024), Image.Resampling.BICUBIC))
            mask_image = Image.fromarray(mask.astype(np.uint8) * 255)
            high_mask = np.array(mask_image.resize((1024, 1024), Image.Resampling.NEAREST)) > 0
            restored = model_output(model, high_image, high_mask, seed)
            return np.array(Image.fromarray(restored).resize((SIZE, SIZE), Image.Resampling.BICUBIC))

        return upscale_inpaint
    if name in ("mat", "powerpaint"):
        from additional_models import load_additional_model

        return load_additional_model(name, device, models_dir)
    return load_model(name, device, models_dir)


def frozen_cases(run_dir, model):
    prepared = read_json(run_dir / "prepared.json")
    expected = "sensitivity-v1" if model in SENSITIVITY_MODELS else "native-v2"
    if prepared["protocol"] != expected:
        raise ValueError(f"{model} does not use protocol {prepared['protocol']}")
    masks = {}
    for case in prepared["cases"]:
        original = run_dir / "originals" / f"{case['case_id']}.png"
        if sha256(original) != case["crop_sha256"]:
            raise ValueError(f"Frozen crop changed: {case['case_id']}")
        masks[case["mask_file"]] = case["mask_sha256"]
    for name, digest in masks.items():
        if sha256(run_dir / "masks" / name) != digest:
            raise ValueError(f"Frozen mask changed: {name}")
    return prepared["cases"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare-sensitivity", "prepare-native", "smoke", "run"))
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--models-dir", type=Path)
    parser.add_argument("--model", choices=(*SENSITIVITY_MODELS, *NATIVE_MODELS))
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()
    if args.stage == "prepare-sensitivity":
        if args.baseline is None:
            parser.error("prepare-sensitivity requires --baseline")
        freeze_sensitivity(args.baseline, args.run_dir)
        return
    if args.stage == "prepare-native":
        if args.manifest is None or args.data_dir is None:
            parser.error("prepare-native requires --manifest and --data-dir")
        prepare_native(args.manifest, args.data_dir, args.run_dir)
        return
    if args.model is None or args.models_dir is None:
        parser.error("smoke and run require --model and --models-dir")
    if args.stage == "smoke":
        smoke(args, model_loader=followup_model)
    else:
        outcome = run(args, cases=frozen_cases(args.run_dir, args.model),
                      model_loader=followup_model, seeds=(PAIRED_SEED,))
        if outcome["failed"]:
            raise SystemExit(2)


if __name__ == "__main__":
    main()
