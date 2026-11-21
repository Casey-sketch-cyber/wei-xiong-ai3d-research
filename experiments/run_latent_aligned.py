"""Rerun frozen painting cases with latent-cell coverage and original-mask scoring."""
import argparse
import shutil
from functools import partial
from pathlib import Path

import numpy as np
from PIL import Image

from additional_models import _load_powerpaint
from latent_aligned import aligned_prediction, grid_cover
from models import load_model
from run_followup import NATIVE_MAIN_PROTOCOL, followup_model, prepared_dirs
from run_pilot import SEEDS, model_output, read_json, run, sha256, smoke, write_json

PROTOCOL = "latent-alignment-v1"
FIRST_SEED = SEEDS[:1]
NATIVE_AIC_PROTOCOL = "native-aic-v1"
UNEXPANDED_DIFFUSION = "native-main-unexpanded-diffusion"
POWERPAINT_REPLAY = "native-review-pp-replay"
POWERPAINT_BLOCK = "The PowerPaint base safety checker withheld the generated image"
ARMS = {
    "baseline": ("procedural-v1", {"sdxl": SEEDS}),
    "baseline-shared": ("procedural-v1", {"lama": FIRST_SEED}),
    "sensitivity": ("sensitivity-v1", {"sdxl_1024": FIRST_SEED, "sdxl_empty": FIRST_SEED}),
    "sensitivity-shared": ("sensitivity-v1", {"lama": FIRST_SEED}),
    "native": ("native-v2", {"sdxl": FIRST_SEED, "powerpaint": FIRST_SEED}),
    "native-shared": ("native-v2", {"lama": FIRST_SEED, "mat": FIRST_SEED}),
    "official-baseline": ("procedural-v1", {"sdxl": FIRST_SEED}),
    "official-1024": ("sensitivity-v1", {"sdxl_1024": FIRST_SEED}),
    "official-native": ("native-v2", {"sdxl": FIRST_SEED}),
    "gray-baseline": ("procedural-v1", {"sdxl": FIRST_SEED}),
    "ring-baseline": ("procedural-v1", {"sdxl": FIRST_SEED}),
    "gray-native": ("native-v2", {"sdxl": FIRST_SEED}),
    "ring-native": ("native-v2", {"sdxl": FIRST_SEED}),
    "native-main": (NATIVE_MAIN_PROTOCOL, {"sdxl": FIRST_SEED, "powerpaint": FIRST_SEED}),
    "native-main-shared": (NATIVE_MAIN_PROTOCOL, {"lama": FIRST_SEED, "mat": FIRST_SEED}),
    "native-main-original": (NATIVE_MAIN_PROTOCOL, {"lama": FIRST_SEED, "mat": FIRST_SEED}),
    UNEXPANDED_DIFFUSION: (NATIVE_MAIN_PROTOCOL, {"sdxl": FIRST_SEED, "powerpaint": FIRST_SEED}),
    "native-review-sdxl": (NATIVE_MAIN_PROTOCOL, {"sdxl": FIRST_SEED}),
    POWERPAINT_REPLAY: (NATIVE_MAIN_PROTOCOL, {"powerpaint": FIRST_SEED}),
    "aic-replication": (NATIVE_AIC_PROTOCOL, {"sdxl": FIRST_SEED, "powerpaint": FIRST_SEED}),
    "aic-replication-shared": (NATIVE_AIC_PROTOCOL, {"lama": FIRST_SEED, "mat": FIRST_SEED}),
    "aic-replication-original": (NATIVE_AIC_PROTOCOL, {"lama": FIRST_SEED, "mat": FIRST_SEED}),
}
OFFICIAL_SDXL_SETTINGS = {"strength": 0.99, "num_inference_steps": 20, "guidance_scale": 8.0}
PREFILL_ARMS = {
    "gray-baseline": "gray", "ring-baseline": "ring", "gray-native": "gray", "ring-native": "ring",
    "native-review-sdxl": "ring",
}
NATIVE_MAIN_APERTURES = {
    "native-main": "shared_grid8",
    "native-main-shared": "shared_grid8",
    "native-main-original": "original",
    UNEXPANDED_DIFFUSION: "original",
    "native-review-sdxl": "shared_grid8",
    POWERPAINT_REPLAY: "shared_grid8",
    "aic-replication": "shared_grid8",
    "aic-replication-shared": "shared_grid8",
    "aic-replication-original": "original",
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


def blocked_powerpaint(main_run, source_digest, source_cases):
    plan_path = main_run / "prepared.json"
    plan = read_json(plan_path)
    if (
        plan["protocol"] != PROTOCOL or plan["arm"] != "native-main"
        or plan["reference_plan_sha256"] != source_digest or plan["cases"] != source_cases
    ):
        raise ValueError("Replay requires the verified CMA main experiment")
    hashes = {}
    for case in source_cases:
        case_id = case["case_id"]
        stem = f"{case_id}__powerpaint__s{FIRST_SEED[0]}"
        failure = main_run / "failures" / f"{stem}.json"
        scored = (main_run / "scores" / f"{stem}.json").is_file()
        output = (main_run / "restored" / f"{stem}.png").is_file()
        if failure.is_file():
            if scored or output or read_json(failure) != {"attempts": 2, "error": POWERPAINT_BLOCK}:
                raise ValueError(f"Replay requires an original safety failure: {case_id}")
            hashes[case_id] = sha256(failure)
        elif not (scored and output):
            raise ValueError(f"Missing PowerPaint completion or safety failure: {case_id}")
    if len(hashes) != 79:
        raise ValueError("Replay requires the 79 original safety failures")
    return {
        "safety_checker": "disabled_replay_only",
        "blocked_reference_plan_sha256": sha256(plan_path),
        "blocked_failure_sha256": hashes,
    }


def freeze(arm, source, target, blocked_reference=None):
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
    replay = (
        blocked_powerpaint(blocked_reference, reference_digest, original_plan["cases"])
        if arm == POWERPAINT_REPLAY else {}
    )
    metadata = {"safety_checker": "enabled"} if arm == UNEXPANDED_DIFFUSION else replay
    init_prefill = PREFILL_ARMS.get(arm)
    input_aperture = NATIVE_MAIN_APERTURES.get(arm)
    settings = OFFICIAL_SDXL_SETTINGS if arm.startswith("official-") or init_prefill else None
    lock = target / "prepared.json"
    if lock.exists():
        existing = read_json(lock)
        if (
            existing["protocol"] != PROTOCOL or existing["arm"] != arm
            or existing["reference_plan_sha256"] != reference_digest
            or existing.get("inference_settings") != settings
            or existing.get("init_prefill") != init_prefill
            or existing.get("input_aperture") != input_aperture
            or any(existing.get(key) != value for key, value in metadata.items())
        ):
            raise ValueError("Target already contains a different frozen plan")
        check_frozen_inputs(target, existing["cases"])
        print(f"{arm}: recovered {len(existing['cases'])} frozen cases", flush=True)
        return

    cases = [case for case in original_plan["cases"]
             if not replay or case["case_id"] in replay["blocked_failure_sha256"]]
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
    prepared = {
        "protocol": PROTOCOL, "arm": arm, "reference_plan_sha256": reference_digest,
        "reference_protocol": expected_protocol, "model_seeds": {key: list(value) for key, value in models.items()},
        "input_mask_areas": input_areas, "cases": cases, **metadata,
    }
    if settings is not None:
        prepared["inference_settings"] = settings
    if init_prefill is not None:
        prepared["init_prefill"] = init_prefill
    if input_aperture is not None:
        prepared["input_aperture"] = input_aperture
    write_json(lock, prepared)
    print(f"{arm}: froze {len(cases)} cases, {len(masks)} scoring masks", flush=True)


def load_aligned_model(name, device, models_dir):
    # Resizing is controlled here, so load the native SDXL pipeline for the 1024 arm.
    return followup_model("sdxl" if name == "sdxl_1024" else name, device, models_dir)


def load_official_sdxl(_name, device, models_dir, *, init_prefill="black"):
    return load_model("sdxl", device, models_dir, init_prefill=init_prefill, **OFFICIAL_SDXL_SETTINGS)


def load_replay_powerpaint(_name, device, models_dir):
    return _load_powerpaint(device, models_dir, safety_checker_enabled=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "smoke", "run"))
    parser.add_argument("--arm", choices=tuple(ARMS), required=True)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--blocked-reference", type=Path)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--models-dir", type=Path)
    parser.add_argument("--model")
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()
    replay = args.arm == POWERPAINT_REPLAY
    if replay and (args.reference is None or args.blocked_reference is None or args.stage == "smoke"):
        parser.error("PowerPaint replay requires both CMA reference paths and a frozen run")
    if args.stage == "prepare":
        if args.reference is None:
            parser.error("prepare requires --reference")
        freeze(args.arm, args.reference, args.run_dir, args.blocked_reference)
        return
    _, models = ARMS[args.arm]
    if args.model not in models or args.models_dir is None:
        parser.error(f"{args.stage} requires --models-dir and a model from {', '.join(models)}")
    inference_size = 1024 if args.model == "sdxl_1024" else 512
    stride = 4 if args.arm == "sensitivity-shared" else 8
    input_aperture = NATIVE_MAIN_APERTURES.get(args.arm)
    predict = model_output if input_aperture == "original" else partial(
        aligned_prediction, inference_size=inference_size, stride=stride,
    )
    init_prefill = PREFILL_ARMS.get(args.arm)
    official = args.arm.startswith("official-") or init_prefill is not None
    model_loader = partial(load_official_sdxl, init_prefill=init_prefill or "black") if official else load_aligned_model
    if replay:
        model_loader = load_replay_powerpaint
    if args.stage == "smoke":
        smoke(args, model_loader=model_loader, predictor=predict)
        return
    prepared = read_json(args.run_dir / "prepared.json")
    if prepared["protocol"] != PROTOCOL or prepared["arm"] != args.arm:
        raise ValueError("Run directory does not match the specified alignment arm")
    expected_seeds = models[args.model]
    if prepared["model_seeds"][args.model] != list(expected_seeds):
        raise ValueError("Run seed schedule differs from the frozen design")
    if official and prepared.get("inference_settings") != OFFICIAL_SDXL_SETTINGS:
        raise ValueError("Run settings differ from the frozen design")
    if prepared.get("init_prefill") != init_prefill:
        raise ValueError("Run fill differs from the frozen design")
    if prepared.get("input_aperture") != input_aperture:
        raise ValueError("Run input aperture differs from the frozen design")
    if args.arm == UNEXPANDED_DIFFUSION and (
        prepared.get("safety_checker") != "enabled" or prepared.get("inference_settings") is not None
    ):
        raise ValueError("Unexpanded diffusion requires the main inference settings and safety checker")
    cases = prepared["cases"]
    if replay:
        source = args.reference / "prepared.json"
        original_cases = read_json(source)["cases"]
        source_digest = sha256(source)
        eligibility = blocked_powerpaint(args.blocked_reference, source_digest, original_cases)
        expected_cases = [case for case in original_cases if case["case_id"] in eligibility["blocked_failure_sha256"]]
        if (
            prepared["reference_plan_sha256"] != source_digest or cases != expected_cases
            or any(prepared.get(key) != value for key, value in eligibility.items())
        ):
            raise ValueError("PowerPaint replay cases differ from the frozen safety records")
    check_frozen_inputs(args.run_dir, cases)
    outcome = run(args, cases=cases, model_loader=model_loader,
                  seeds=expected_seeds, predictor=predict, max_attempts=1 if replay else 2)
    if outcome["failed"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
