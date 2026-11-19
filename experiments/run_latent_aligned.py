"""Rerun frozen painting cases with latent-cell coverage and original-mask scoring."""
import argparse
import shutil
from functools import partial
from pathlib import Path

import numpy as np
from PIL import Image

from latent_aligned import aligned_prediction, grid_cover
from run_followup import followup_model, prepared_dirs
from run_pilot import SEEDS, read_json, run, sha256, smoke, write_json

PROTOCOL = "latent-alignment-v1"
FIRST_SEED = SEEDS[:1]
ARMS = {
    "baseline": ("procedural-v1", {"sdxl": SEEDS}),
    "baseline-shared": ("procedural-v1", {"lama": FIRST_SEED}),
    "sensitivity": ("sensitivity-v1", {"sdxl_1024": FIRST_SEED, "sdxl_empty": FIRST_SEED}),
    "sensitivity-shared": ("sensitivity-v1", {"lama": FIRST_SEED}),
    "native": ("native-v2", {"sdxl": FIRST_SEED, "powerpaint": FIRST_SEED}),
    "native-shared": ("native-v2", {"lama": FIRST_SEED, "mat": FIRST_SEED}),
}


def check_frozen_inputs(root, cases):
    masks = {}
    for case in cases:
        crop = root / "originals" / f"{case['case_id']}.png"
        if sha256(crop) != case["crop_sha256"]:
            raise ValueError(f"Frozen crop changed: {case['case_id']}")
        masks[case["mask_file"]] = case["mask_sha256"]
    for filename, digest in masks.items():
        if sha256(root / "masks" / filename) != digest:
            raise ValueError(f"Frozen scoring mask changed: {filename}")
    return masks


def freeze(arm, source, target):
    if target.resolve().is_relative_to(source.resolve()) or source.resolve().is_relative_to(target.resolve()):
        raise ValueError("Reference and rerun directories must be separate")
    reference = source / "prepared.json"
    original_plan = read_json(reference)
    expected_protocol, models = ARMS[arm]
    if original_plan["protocol"] != expected_protocol:
        raise ValueError(f"{arm} requires a {expected_protocol} prepared reference")
    if not original_plan["cases"]:
        raise ValueError("No prepared cases")
    reference_digest = sha256(reference)
    lock = target / "prepared.json"
    if lock.exists():
        existing = read_json(lock)
        if (
            existing["protocol"] != PROTOCOL or existing["arm"] != arm
            or existing["reference_plan_sha256"] != reference_digest
        ):
            raise ValueError("Target already contains a different frozen plan")
        check_frozen_inputs(target, existing["cases"])
        print(f"{arm}: recovered {len(existing['cases'])} frozen cases", flush=True)
        return

    cases = original_plan["cases"]
    masks = check_frozen_inputs(source, cases)
    prepared_dirs(target)
    for case in cases:
        name = Path("originals") / f"{case['case_id']}.png"
        shutil.copyfile(source / name, target / name)
    input_areas = {}
    for filename in masks:
        name = Path("masks") / filename
        shutil.copyfile(source / name, target / name)
        with Image.open(target / name) as image:
            mask = np.array(image) > 0
        input_areas[filename] = {
            "score_pixels": int(mask.sum()),
            "reference_stride8_pixels": int(grid_cover(mask, 8).sum()),
            "reference_stride4_pixels": int(grid_cover(mask, 4).sum()),
        }
    write_json(lock, {
        "protocol": PROTOCOL, "arm": arm, "reference_plan_sha256": reference_digest,
        "reference_protocol": expected_protocol, "model_seeds": {key: list(value) for key, value in models.items()},
        "input_mask_areas": input_areas, "cases": cases,
    })
    print(f"{arm}: froze {len(cases)} cases, {len(masks)} scoring masks", flush=True)


def load_aligned_model(name, device, models_dir):
    # Resizing is controlled here, so load the native SDXL pipeline for the 1024 arm.
    return followup_model("sdxl" if name == "sdxl_1024" else name, device, models_dir)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "smoke", "run"))
    parser.add_argument("--arm", choices=tuple(ARMS), required=True)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--models-dir", type=Path)
    parser.add_argument("--model")
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()
    if args.stage == "prepare":
        if args.reference is None:
            parser.error("prepare requires --reference")
        freeze(args.arm, args.reference, args.run_dir)
        return
    _, models = ARMS[args.arm]
    if args.model not in models or args.models_dir is None:
        parser.error(f"{args.stage} requires --models-dir and a model from {', '.join(models)}")
    inference_size = 1024 if args.model == "sdxl_1024" else 512
    stride = 4 if args.arm == "sensitivity-shared" else 8
    predict = partial(aligned_prediction, inference_size=inference_size, stride=stride)
    if args.stage == "smoke":
        smoke(args, model_loader=load_aligned_model, predictor=predict)
        return
    prepared = read_json(args.run_dir / "prepared.json")
    if prepared["protocol"] != PROTOCOL or prepared["arm"] != args.arm:
        raise ValueError("Run directory does not match the specified alignment arm")
    expected_seeds = models[args.model]
    if prepared["model_seeds"][args.model] != list(expected_seeds):
        raise ValueError("Run seed schedule differs from the frozen design")
    cases = prepared["cases"]
    check_frozen_inputs(args.run_dir, cases)
    outcome = run(args, cases=cases, model_loader=load_aligned_model,
                  seeds=expected_seeds, predictor=predict)
    if outcome["failed"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
